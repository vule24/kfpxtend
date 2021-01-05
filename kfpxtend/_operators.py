from kfp import dsl
from pathlib import Path


class NotebookOp(dsl.ContainerOp):
    """Represents an op implemented by a Notebook and dependencies.
    
    Args:
        notebook: path to notebook.
        dependencies: path to dependencies dir.
        gcs_bucket: Google Cloud Storage bucket.
        gcs_directory: GCS dir in gcs_bucket.
        version: tag version for each notebook run. If not define,
            version will be set to `%Y-%m-%d_%H:%M:%S` format.
        kwargs: all the arguments for ContainerOp.
        
    Note: 
        - This Op need to be initialized inside pipeline definition or inside a function
            that return an Op for triggering upload source to GCS whenever sources are updated.
        - NotebookOp use celltags: `params` to set parameters and `skip` to ignore cells, 
            others would be use as main source.
        - If arguments include list or dict, we can define them in string.
            Eg. ['--a', '"[1,2,3]"',
                 '--b', '\\"{"key1": 1, "key2": "value"}\\"']
        - Remember to save your Notebook before defining pipeline.
    Example: 
        >>> @dsl.pipeline(
        ...     name="test",
        ...     description="test"
        ... )
        ... def pipeline():
        ...     op = NotebookOp(
        ...         notebook='path/to/notebook.ipynb',
        ...         dependencies='path/to/dependencies',
        ...         gcs_bucket='bucket_name',
        ...         gcs_directory='path/to/gsc_directories',
        ...         version='test',
        ...         name='NotebookOpTest',
        ...         image='path/image:tag',
        ...         arguments=['--a', '"[1,2,3]"',
        ...                    '--b', '5']
        ...     )
    """
    def __init__(self,
                 notebook:str,
                 dependencies:str,
                 gcs_bucket:str,
                 gcs_directory:str,
                 version:str=None,
                 **kwargs):
        self.notebook = Path(notebook.strip())
        self.dependencies = Path(dependencies.strip('/')) if dependencies else None
        self.gcs_bucket = gcs_bucket.strip('/')
        self.gcs_directory = gcs_directory.strip('/')
        self.zipname = ''
        self.version = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") if not version else version

        assert self.notebook.suffix == '.ipynb'
        if not notebook:
            raise ValueError("You need to provide a notebook.")
            
        if 'name' not in kwargs:
            raise TypeError("You need to provide a name for the operation.")
        elif not kwargs.get('name'):
            raise ValueError("You need to provide a name for the operation.")
        self.zipname = f"{kwargs['name']}_{self.version}.zip"

        if 'image' not in kwargs:
            raise ValueError("You need to provide an image.")
            
        kwargs['command'] = ['sh', '-c']
        kwargs['arguments'] = ''.join(
            [(f'echo "SETUP:\n------" && '
              f'gsutil -m cp -r gs://{self.gcs_bucket}/{self.gcs_directory}/{self.zipname} . && '
              f'python3 -m zipfile -e {self.zipname} . && '
              f'echo "\nSOURCE:\n-------" && '
              f'python3 nb_convert.py && '
              f'echo "\nLOG:\n----" && '
              f'python3 {self.notebook.with_suffix(".py").name} '), 
             ' '.join(kwargs.get('arguments', []))]
        )
        
        self.upload_all()
        super().__init__(**kwargs)
        
    
    def get_converter_source(self):
        import inspect, os
        converter_src = list(filter('\n'.__ne__, inspect.getsourcelines(self.convert)[0][1:]))
        common = os.path.commonprefix(converter_src)
        ret = [line[len(common):] for line in converter_src]
        for i,line in enumerate(ret):
            ret[i] = line.replace("nb_path = Path(f'{notebook}')", f"nb_path = Path(f'{self.notebook.name}')")
        return r'{}'.format(''.join(ret))
        
    def convert(self, notebook):
        import json
        import itertools
        from pathlib import Path

        nb_path = Path(f'{notebook}')
        ipynb = json.loads(nb_path.read_text())
        cells = [cell for cell in ipynb['cells'] if cell['cell_type'] == 'code' and 'skip' not in cell['metadata'].get('tags', [])]

        params = list(itertools.chain.from_iterable([cell['source'] for cell in cells if 'params' in cell['metadata'].get('tags', [])]))
        source = list(itertools.chain.from_iterable([cell['source'] for cell in cells if 'params' not in cell['metadata'].get('tags', [])]))

        main_src = ('import argparse\n'
                    'import ast\n'
                    'import subprocess\n'
                    'parser = argparse.ArgumentParser()\n')

        params = list(map(lambda x: x.strip(), params))
        lvalues = []
        for expression in params:
            lvalue = expression.split('=')[0].strip()
            lvalues.append(lvalue)

        add_arguments = casts = ''
        for arg in lvalues:
            add_arguments += f"parser.add_argument('--{arg[0]}', type=str, required=True)\n"
            casts += f"{arg[0]} = ast.literal_eval(args.{arg[0]})\n"

        main_src = ''.join([main_src, add_arguments, "args = parser.parse_args()\n", casts]) + '\n'.join(map(lambda x: x.strip('\n'), source))
        main_src = main_src.split('\n')
        for i, line in enumerate(main_src):
            if line.strip().startswith('!'):
                bashcmd = line.strip()[1:]
                main_src[i] = (f"bashcmd = '{bashcmd}'\n"
                               f"process = subprocess.Popen(bashcmd.split(), stdout=subprocess.PIPE)\n"
                               f"output, _ = process.communicate()\n"
                               f"print(output.decode('utf-8'))\n")
        main_src = '\n'.join(main_src)        
        nb_path.with_suffix('.py').write_text(main_src)

        n_lineno = len(str(len(main_src.split('\n'))))
        for i, line in enumerate(main_src.split('\n')):
            print(f'{i:>{n_lineno}}| {line}')
            
    def upload_all(self):
        with zipfile.ZipFile(f'/tmp/{self.zipname}', 'w', zipfile.ZIP_DEFLATED) as zip_obj:
            zip_obj.write(self.notebook)
            zip_obj.writestr('nb_convert.py', self.get_converter_source())
            if self.dependencies:
                for file in self.dependencies.glob('**/*'):
                    zip_obj.write(file)
        
        cmd = f'gsutil -m cp -r /tmp/{self.zipname} gs://{self.gcs_bucket}/{self.gcs_directory}/{self.zipname}'
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        
        return self


class PythonFileOp(dsl.ContainerOp):
    """Represents an op implemented by a PythonFile and dependencies.
    
    Args:
        pyfile: path to PythonFile.
        dependencies: path to dependencies dir.
        gcs_bucket: Google Cloud Storage bucket.
        gcs_directory: GCS dir in gcs_bucket.
        version: tag version for each pythonfile run. If not define,
            version will be set to `%Y-%m-%d_%H:%M:%S` format.
        kwargs: all the arguments for ContainerOp.
        
    Note: 
        - This Op need to be initialized inside pipeline definition or inside a function
            that return an Op for triggering upload source to GCS whenever sources are updated.
        - PythonFile use comments: `# params` after assign statement to set parameters, 
            others would be use as main source.
        - If arguments include list or dict, we can define them in string.
            Eg. ['--a', '"[1,2,3]"',
                 '--b', '\\"{"key1": 1, "key2": "value"}\\"']
        - Remember to save your Notebook before defining pipeline.
    Example: 
        >>> @dsl.pipeline(
        ...     name="test",
        ...     description="test"
        ... )
        ... def pipeline():
        ...     op = PythonFileOp(
        ...         pyfile='path/to/pyfile.py',
        ...         dependencies='path/to/dependencies',
        ...         gcs_bucket='bucket_name',
        ...         gcs_directory='path/to/gsc_directories',
        ...         version='test',
        ...         name='PythonFileOpTest',
        ...         image='path/image:tag',
        ...         arguments=['--a', '"[1,2,3]"',
        ...                    '--b', '5']
        ...     )
    """
    def __init__(self,
                 pyfile:str,
                 dependencies:str,
                 gcs_bucket:str,
                 gcs_directory:str,
                 version:str=None,
                 **kwargs):
        self.pyfile = Path(pyfile.strip())
        self.dependencies = Path(dependencies.strip('/')) if dependencies else None
        self.gcs_bucket = gcs_bucket.strip('/')
        self.gcs_directory = gcs_directory.strip('/')
        self.zipname = ''
        self.version = datetime.now().strftime("%Y-%m-%d_%H:%M:%S") if not version else version

        assert self.pyfile.suffix == '.py'
        if not pyfile:
            raise ValueError("You need to provide a PythonFile.")
            
        if 'name' not in kwargs:
            raise TypeError("You need to provide a name for the operation.")
        elif not kwargs.get('name'):
            raise ValueError("You need to provide a name for the operation.")
        self.zipname = f"{kwargs['name']}_{self.version}.zip"

        if 'image' not in kwargs:
            raise ValueError("You need to provide an image.")
            
        kwargs['command'] = ['sh', '-c']
        kwargs['arguments'] = ''.join(
            [('echo "SETUP:\n------" && '
              f'gsutil -m cp -r gs://{self.gcs_bucket}/{self.gcs_directory}/{self.zipname} . && '
              f'python3 -m zipfile -e {self.zipname} . && '
              f'echo "\nSOURCE:\n-------" && '
              f'python3 nb_convert.py && '
              f'echo "\nLOG:\n----" && '
              f'python3 src_{self.pyfile.name} '), 
             ' '.join(kwargs.get('arguments', []))]
        )
        
        self.upload_all()
        super().__init__(**kwargs)
        
    def get_converter_source(self):
        import inspect, os
        converter_src = list(filter('\n'.__ne__, inspect.getsourcelines(self.convert)[0][1:]))
        common = os.path.commonprefix(converter_src)
        ret = [line[len(common):] for line in converter_src]
        for i,line in enumerate(ret):
            ret[i] = line.replace("pyfile_path = Path(f'{pyfile}')", f"pyfile_path = Path(f'{self.pyfile}')")
        return r'{}'.format(''.join(ret))
        
    def convert(self, pyfile):
        import itertools
        from pathlib import Path

        pyfile_path = Path(f'{pyfile}')
        py = pyfile_path.read_text().split('\n')

        main_src = ('import argparse\n'
                    'import ast\n'
                    'parser = argparse.ArgumentParser()\n')

        lvalues = []
        first_params_idx = len(py)
        for line in reversed(py):
            if not line.replace(' ','').endswith('#params'):
                continue
            sharp_idx = line.find('#')
            expresion = line[:sharp_idx]
            lvalue = expresion.split('=')[0].strip()
            lvalues.append(lvalue)
            i = py.index(line)
            if i < first_params_idx:
                first_params_idx = i
                py.remove(line)
        py.insert(first_params_idx, '{}')

        add_arguments = casts = ''
        for arg in reversed(lvalues):
            add_arguments += f"parser.add_argument('--{arg[0]}', type=str, required=True)\n"
            casts += f"{arg[0]} = ast.literal_eval(args.{arg[0]})\n"

        main_src = '\n'.join(py).format(''.join([main_src, add_arguments, "args = parser.parse_args()\n", casts]))

        pyfile_path.with_name(f'src_{pyfile_path.name}').write_text(main_src)

        n_lineno = len(str(len(main_src.split('\n'))))
        for i, line in enumerate(main_src.split('\n')):
            print(f'{i:>{n_lineno}}| {line}')

    def upload_all(self):
        with zipfile.ZipFile(f'/tmp/{self.zipname}', 'w', zipfile.ZIP_DEFLATED) as zip_obj:
            zip_obj.write(self.pyfile)
            zip_obj.writestr('nb_convert.py', self.get_converter_source())
            if self.dependencies:
                for file in self.dependencies.glob('**/*'):
                    zip_obj.write(file)
        
        cmd = f'gsutil -m cp -r /tmp/{self.zipname} gs://{self.gcs_bucket}/{self.gcs_directory}/{self.zipname}'
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        
        return self