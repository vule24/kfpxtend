import kfp
from datetime import datetime
from functools import wraps
import pytz


def func_to_container_op(base_image:str):
    """Rewrite func_to_container_op decorator of kfp.
    Parameters
    ----------
    base_image: [str]
        Base image for container op
    Return
    ------
    [Callable]
    Decorator of kubeflow sdk with base_image defined"""
    def _func_to_container_op(func):
        func = kfp.components.func_to_container_op(func, base_image=base_image)
        return func
    return _func_to_container_op

def _exception_handler(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            return None
    return _wrapper


def show_help():
    print('Give easykubeflow a \U0001F31F on github\nLink to Examples https://github.com/vule24/easykubeflow/tree/master/examples')
    

class Utils:
    
    def __init__(self, client):
        """Constructor of Utils.
        Parameters
        ----------
        client: kfp._client.Client
            Kubeflow sdk Client object.
            
        Usage
        -----
        >>> import kfp
        >>> from utils import Utils
        >>> client = kfp.Client()
        >>> Utils(client)
        """
        self.page_size = 500
        self.client = client
        self.client.get_experiment_by_name = self.get_experiment_by_name
        self.client.get_run_by_name = self.get_run_by_name
        self.client.get_pipeline_by_name = self.get_pipeline_by_name
        self.client.get_runs_by_experiment = self.get_runs_by_experiment
        self.client.delete_pipeline_by_name = self.delete_pipeline_by_name
        self.client.delete_experiment_by_name = self.delete_experiment_by_name
        self.client.delete_run_by_name = self.delete_run_by_name
        self.client.delete_runs_by_experiment = self.delete_runs_by_experiment
        self.client.upload_pipeline_version = self.upload_pipeline_version
        
        print('easykubeflow.show_help() to get examples source')
        
        
    @_exception_handler
    def get_pipeline_by_name(self, name):
        """Get pipeline using its name.
        Parameters
        ----------
        name: str
            Name of pipeline.
            
        Returns
        -------
        str
            ID of pipeline
        """
        next_page_token = ''
        while True:
            pipelines_info = self.client.pipelines.list_pipelines(page_token=next_page_token, page_size=self.page_size)
            next_page_token = pipelines_info.next_page_token
            for pipeline in pipelines_info.pipelines:
                if pipeline.name == name:
                    return pipeline.id
            if next_page_token is None:
                break
        return ''

    @_exception_handler
    def get_experiment_by_name(self, name):
        """Get experiment using its name.
        Parameters
        ----------
        name: str
            Name of experiment.
            
        Returns
        -------
        str
            ID of experiment.
        """
        next_page_token = ''
        while True:
            exps_info = self.client.experiments.list_experiment(page_token=next_page_token,page_size=self.page_size)
            next_page_token = exps_info.next_page_token
            for exp in exps_info.experiments:
                if exp.name == name:
                    return exp.id
            if next_page_token is None:
                break
        return ''
    
    @_exception_handler
    def get_run_by_name(self, name, level:str='easy'):
        """Get run using its name.
        Parameters
        ----------
        name: str
            Name of run.
        level: str
            If `hard`, retrieve run till the last page.
            If `easy`, find the latest runs in the first page with `page_size` elements.
            
        Returns
        -------
        List[str]
            List of ids.
        """
        run_ids = []
        if level == 'easy':
            for run in self.client.runs.list_runs(page_size=self.page_size).runs:
                if run.name == name:
                    run_ids.append(run.id)
        elif level == 'hard':
            next_page_token = ''
            while True:
                runs_info = self.client.runs.list_runs(page_token=next_page_token, page_size=self.page_size)
                next_page_token = runs_info.next_page_token
                for run in runs_info.runs:
                    if run.name == name:
                        run_ids.append(run.id)
                if next_page_token is None:
                    break
        return run_ids
    
    @_exception_handler
    def get_runs_by_experiment(self, exp_name, level:str='easy'):
        """Get runs that belongs to an experiment.
        Parameters
        ----------
        exp_name: str
            Experiment name.
        level: str
            If `hard`, retrieve run till the last page even if the exp_name has been removed.
            If `normal`, retrieve run till the last page when exp_name still exists.
            If `easy`, find the latest runs in the first page with `page_size` elements.
            
        Returns
        -------
        Dict[str, str]
            Dictionary of runs in experiment.
        """
        run_name_ids = []
        if level == 'easy':
            for run in self.client.runs.list_runs(page_size=self.page_size).runs:
                if run.resource_references[0].name == exp_name:
                    run_name_ids.append({'name': run.name, 'id': run.id})
        elif level == 'normal':
            exp_id = self.get_experiment_by_name(exp_name)
            if not exp_id:
                print(f'Experiment: {exp_name} not exists')
                return {}
            next_page_token = ''
            while True:
                runs_info = self.client.list_runs(page_token=next_page_token, page_size=self.page_size, experiment_id=exp_id)
                next_page_token = runs_info.next_page_token
                for run in runs_info.runs:
                    run_name_ids.append({'name': run.name, 'id': run.id})
                if next_page_token is None:
                    break
        elif level == 'hard':
            next_page_token = ''
            while True:
                runs_info = self.client.list_runs(page_token=next_page_token, page_size=self.page_size)
                next_page_token = runs_info.next_page_token
                for run in runs_info.runs:
                    is_match_exp = False
                    for resource in run.resource_references:
                        if resource.key.type=='EXPERIMENT':
                            is_match_exp=True if resource.name == exp_name else False
                            break
                    if is_match_exp:
                        run_name_ids.append({'name': run.name, 'id': run.id})
                if next_page_token is None:
                    break
        else:
            raise NotImplementedError
        return run_name_ids
            
    @_exception_handler
    def delete_pipeline_by_name(self, name):
        """Delete pipeline using its name.
        Parameters
        ----------
        name: str
            Name of pipeline to be deleted.
        """
        pipeline_id = self.get_pipeline_by_name(name)        
        self.client.pipelines.delete_pipeline(pipeline_id)
        print(f'Deleted pipeline\tName: {name}\tID: {pipeline_id}')
        
    @_exception_handler
    def delete_experiment_by_name(self, name):
        """Delete experiment using its name.
        Parameters
        ----------
        name: str
            Name of experiment to be deleted.
        """
        exp_id = self.get_experiment_by_name(name)
        self.client.experiments.delete_experiment(exp_id)
        print(f'Deleted experiment\tName: {name}\tID: {exp_id}')
        
    @_exception_handler
    def delete_run_by_name(self, name, level:str='easy'):
        """Delete run using its name.
        Parameters
        ----------
        name: str
            Name of run to be deleted.
        level: str
            If `hard`, retrieve run till the last page.
            If `easy`, find the latest runs in the first page with `page_size` elements.
        """
        run_ids = self.get_run_by_name(name, level)
        print(f'Total: {len(run_ids)} runs')
        for i, run_id in enumerate(run_ids):
            self.client.runs.delete_run(run_id)
            print(f'Deleted run [{i}]:\tName: {name}\tID: {run_id}')
        
    @_exception_handler
    def delete_runs_by_experiment(self, exp_name, level:str='easy'):
        """Delete runs that belongs to an experiment.
        Parameters
        ----------
        exp_name: str
            Name of experiment.
        level: str
            If `hard`, retrieve run till the last page even if the exp_name has been removed.
            If `normal`, retrieve run till the last page when exp_name still exists.
            If `easy`, find the latest runs in the first page with `page_size` elements.
        """
        name_ids = self.get_runs_by_experiment(exp_name, level)
        print(f'Total: {len(name_ids)} runs')
        for i, run in enumerate(name_ids):
            self.client.runs.delete_run(run["id"])
            print(f'Deleted run [{i}]:\tName: {run["name"]}\tID: {run["id"]}')
            
    @_exception_handler
    def upload_pipeline_version(self, filepath, pipeline_name:str, version:str=None):
        """Upload a version of existing pipeline.
        Parameters
        ----------
        filepath: str
            Path to .yaml file.
        pipeline_name: str
            Name of existing pipeline.
        version: str, optional
            Version of new uploaded pipeline. Defaults to None to get version as timestamp.
        """
        version = '{name}_version_at_{time}'.format(
            name=pipeline_name,
            time=pytz.timezone("Asia/Ho_Chi_Minh").localize(datetime.now()).strftime('%Y-%m-%d_%H:%M:%S')
        ) if version is None else version
        
        try:
            self.client.upload_pipeline(filepath, pipeline_name)
            print('Uploaded new pipeline')
        except:
            pipelineid = self.get_pipeline_by_name(pipeline_name)[0]
            self.client.pipeline_uploads.upload_pipeline_version(
                filepath,
                pipelineid=pipelineid,
                name=version)
            print(f'Uploaded version for {pipeline_name}')