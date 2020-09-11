from datetime import datetime
from functools import wraps
import pytz

def _exception_handler(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
            return None
    return _wrapper
    

class Utils:

    def __init__(self, client):
        """Constructor of Utils.

        Args:
            client (kfp._client.Client): kubeflow sdk Client object.
        """
        self.client = client
    
    def _get_attr(self, prefix, attr):
        """Find `prefix` attribute follows `attr`. In kubeflow client for paticular.

        Args:
            prefix (object): object need to find attribute.
            attr (str): attribute name.

        Returns:
            object: attribute object of `prefix`.
        """
        try:
            return getattr(prefix, attr)
        except:
            return getattr(prefix, attr + 's')
    
    def _get_api(self, attr, page_size=500):
        """Get method of kfp.Client().<api>.

        Args:
            attr (str): could be `pipelines`, `runs`, `experiments`, etc.
            page_size (int, optional): Max size of retrieved list. Defaults to 500.

        Returns:
            object: Respective method.
        """
        api = self._get_attr(self.client, attr)
        api_info = self._get_attr(api, f'list_{attr}')(page_size=page_size)
        return self._get_attr(api_info, attr)
    
    def _get_ids_by_name(self, attr, name):
        """Base method for getting a list of ids following respective api.

        Args:
            attr (str): attribute of kfp.Client().
            name (str): name of needed id.

        Returns:
            List[str]: list of ids.
        """
        ids = []
        for element in self._get_api(attr):
            if name == element.name:
                ids.append(element.id)
        return ids
    
    @_exception_handler
    def get_experiment_by_name(self, name):
        """Get experiment using its name.

        Args:
            name (str): Name of experiment.

        Returns:
            List[str]: List of ids.
        """
        return self._get_ids_by_name('experiment', name)

    @_exception_handler
    def get_run_by_name(self, name):
        """Get run using its name.

        Args:
            name (str): Name of run.

        Returns:
            List[str]: List of ids.
        """
        return self._get_ids_by_name('run', name)

    @_exception_handler
    def get_pipeline_by_name(self, name):
        """Get pipeline using its name.

        Args:
            name (str): Name of pipeline.

        Returns:
            List[str]: List of ids.
        """
        return self._get_ids_by_name('pipeline', name)
    
    @_exception_handler
    def get_runs_by_experiment(self, exp_name):
        """Get runs that belongs to an experiment.

        Args:
            exp_name (str): experiment name.

        Returns:
            List[str]: List of ids.
        """
        id_name = []
        for run in self.client.runs.list_runs(page_size=500).runs:
            if run.resource_references[0].name == exp_name:
                id_name.append((run.id, run.name))
        return id_name
            
    def _delete(self, attr, name):
        """Base delete method.

        Args:
            attr (str): api to use.
            name (str): name to delete.
        """
        _ids = self._get_ids_by_name(attr, name)
        delete_api = self._get_attr(self._get_attr(self.client, attr), f'delete_{attr}')
        for _id in _ids:
            delete_api(_id)
            print(f'Deleted pipeline:\nID: {_id}\nName: {name}')
        
    @_exception_handler
    def delete_pipeline_by_name(self, name):
        """Delete pipeline using its name.

        Args:
            name (str): Name of pipeline to be deleted.
        """
        self._delete('pipeline', name)
            
    @_exception_handler
    def delete_experiment_by_name(self, name):
        """Delete experiment using its name.

        Args:
            name (str): Name of experiment to be deleted.
        """
        self._delete('experiment', name)

    @_exception_handler
    def delete_run_by_name(self, name):
        """Delete run using its name.

        Args:
            name (str): Name of run to be deleted.
        """
        self._delete('run', name)

    @_exception_handler
    def delete_runs_by_experiment(self, exp_name):
        """Delete runs that belongs to an experiment.

        Args:
            exp_name (str): Name of experiment.
        """
        id_name = self.get_runs_by_experiment(exp_name)
        for _id, _name in id_name:
            self.delete_run_by_name(_name)
            print(f'Deleted run:\nID: {_id}\nName: {_name}')
    
    @_exception_handler
    def upload_pipeline_version(self, filepath, pipeline_name:str, version:str=None):
        """Upload a version of existing pipeline.

        Args:
            filepath (str): path to .yaml file.
            pipeline_name (str): Name of existing pipeline.
            version (str, optional): Version of new uploaded pipeline. Defaults to None.
        """
        pipelineid = self.get_pipeline_by_name(pipeline_name)[0]
        version = '{name}_version_at_{time}'.format(
            name=pipeline_name,
            time=pytz.timezone("Asia/Ho_Chi_Minh").localize(datetime.now()).strftime('%Y-%m-%d_%H:%M:%S')
        ) if version is None else version
        
        self.client.pipeline_uploads.upload_pipeline_version(
            filepath,
            pipelineid=pipelineid,
            name=version
        )