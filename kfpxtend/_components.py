import kfp
import kfp.components._components as comp
from typing import Callable, List, Dict, Any, Optional, NamedTuple
from importlib.util import module_from_spec, spec_from_loader
from types import ModuleType
from kfp.components import InputPath, OutputPath
from pathlib import Path
from datetime import datetime
import os.path
import sys
import json
import tempfile
import zipfile
import subprocess


class NotebookComponent:
    """Notebook Component is used to create a component by submitting a notebook and its dependencies to GCS then download, extract the archived zip file and run it at runtime.
    Notebook outputs are visualized as static HTML which could be retrieved at `Artifact` Tab or `Run output` Tab in the Kubeflow Pipeline UI.
    Parameters
    ----------
    notebook: str
        Path to notebook
    dependencies: str
        Path to dependencies
    gs_path: str
        GCS path to store archived zip file
    output_component_file: Optional[str]
        Export yaml format to file
    base_image: Optional[str]
        Image to run notebook
    packages_to_install: Optional[List[str]]
        Additional packages to install at runtime
    params_schema: Optional[Dict[str, Any]]
        Schema for parameters that are defined at notebook cell with "parameters" tag
    remove_nb_inputs: bool
        True to exclude input / input prompt. Default True
    """
    def __init__(
        self, 
        notebook: str,
        dependencies: str,
        gs_path: str,
        output_component_file: Optional[str] = None,
        base_image: Optional[str] = None,
        packages_to_install: Optional[List[str]] = [],
        params_schema: Optional[Dict[str, Any]] = None,
        remove_nb_inputs:bool = True
    ):
        self.notebook = Path(notebook.strip())
        self.dependencies = Path(dependencies.strip()) if dependencies else ''
        self.gs_path = gs_path.rstrip('/')
        self.output_component_file = output_component_file
        self.base_image = base_image
        self.packages_to_install = ["jupyter", "papermill", "nbconvert", "google-cloud-storage"] + packages_to_install
        self.zipname = ''
        self.params_schema = params_schema
        self.remove_nb_inputs = remove_nb_inputs
        
        if not self.notebook.is_file():
            raise "Input Notebook is not exist"
        
        if not self.base_image:
            raise "base_image must be defined"
            
        if not self.gs_path:
            raise "gs_path must be defined"
            
                    
        
    def load_component(self, version: Optional[str]=None):
        """Submit notebook to GCS and create Kubeflow Pipeline component.
        Parameters
        ----------
        version: Optional[str]
            Defined version of Notebook archive zip file. If not defined, version would be "YYYYMMDD_HHMMSS"
        
        Return
        ------
        KF Component
        """
        # Set version for notebook archive
        version = version or datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Zip notebook archive
        self.zipname = f"{self.notebook.name.split('.')[0]}_{version}.zip"
        tmpdir = tempfile.mkdtemp()
        zip_path = Path(tmpdir) / self.zipname
        zip_obj = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED)
        zip_obj.write(self.notebook)
        if self.dependencies:
            for file in self.dependencies.glob('**/*'):
                zip_obj.write(file)
        zip_obj.close()
        
        # Upload notebook archived zip file to GCS
        cmd = f'gsutil -m cp {zip_path} {self.gs_path}/{zip_path.name}'
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
        process.communicate()
        
        if self.params_schema:
            func_params = []
            pm_params = []
            for param_name, type_ in self.params_schema.items():
                func_params.append(f"{param_name}: {type_}")
                pm_params.append(f"'{param_name}': {param_name}")
            func_params = ",".join(func_params)
            pm_params = "{" + f"{','.join(pm_params)}" + "}"
        else:
            func_params = ""
            pm_params = "{}"
            
        execute_func = f"""def NotebookComponent(
    {func_params}
) -> NamedTuple('StaticHTMLOutput', [('mlpipeline_ui_metadata', 'UI_metadata')]):
    '''A wrapper func to run notebook'''
    import zipfile
    import json
    import papermill as pm
    from pathlib import Path
    from google.cloud import storage
    from nbconvert import HTMLExporter
    from traitlets.config import Config
    import os

    client = storage.Client()
    gs_path = '{self.gs_path}'[len('gs://'):].split('/')
    bucket, blob = gs_path[0], '/'.join(gs_path[1:] + ['{zip_path.name}'])
    
    bucket = client.get_bucket(bucket)
    
    blob = bucket.blob(blob)
    blob.download_to_filename('{zip_path.name}')
    
    print('Downloaded: {zip_path.name}')
    
        
    with zipfile.ZipFile('./{zip_path.name}', 'r') as zip_ref:
        zip_ref.extractall('.')
    
    pm.execute_notebook(
        './{self.notebook.name}',
        './output.ipynb',
        parameters={pm_params}
    )
    
    c = Config()
    if {self.remove_nb_inputs} == True:
        c.HTMLExporter.exclude_input_prompt = True
        c.HTMLExporter.exclude_input = True
        
    htmlExporter = HTMLExporter(config=c)
    htmlExporter.template_name = 'classic'
    body, _ = htmlExporter.from_filename('output.ipynb')
                
    metadata = {{
        "version": 1,
        'outputs' : [
        {{
            'type' : 'web-app',
            'storage' : 'inline',
            'source' : body
        }}]
    }}
    
    from collections import namedtuple
    static_html_output = namedtuple('StaticHTMLOutput', ['mlpipeline_ui_metadata'])
    return static_html_output(json.dumps(metadata))"""
        
        _import_script = "from kfp.components import *\nfrom typing import NamedTuple\n"
        execute_func = _import_script + execute_func
                
        filename = tempfile.mktemp(suffix='.py')
        modname = os.path.splitext(os.path.basename(filename))[0]
        assert modname not in sys.modules
        loader = ShowSourceLoader(modname, execute_func)
        spec = spec_from_loader(modname, loader, origin=filename)
        module = module_from_spec(spec)
        code = compile(execute_func, mode='exec', filename=filename)
        exec(code, module.__dict__)
        sys.modules[modname] = module
        
        return kfp.components.create_component_from_func(
            func=module.NotebookComponent,
            output_component_file=self.output_component_file,
            base_image=self.base_image,
            packages_to_install=self.packages_to_install
        )
        
        

class ShowSourceLoader:
    def __init__(self, modname: str, source: str) -> None:
        self.modname = modname
        self.source = source

    def get_source(self, modname: str) -> str:
        if modname != self.modname:
            raise ImportError(modname)
        return self.source

        
    
if __name__ == "__main__":
    from kfp.components import InputPath
    help(NotebookComponent(
        notebook="./Untitled.ipynb",
        dependencies="./kfpxtend",
        gs_path="gs://vinid-data-science-rec-ecart-np/tmp",
        base_image='hihi',
        params_schema={'a': "int", 'bigA': "InputPath('CSV')", 'b': "'GCS Path'"}
    ).load_component())