import kfp
from ._client import *
from ._operators import *
from ._component_store import *
from ._auth import *

kfp.Client.page_size = 500
kfp.Client.get_pipeline_by_name = get_pipeline_by_name
kfp.Client.get_experiment_by_name = get_experiment_by_name
kfp.Client.get_run_by_name = get_run_by_name
kfp.Client.get_runs_by_experiment = get_runs_by_experiment
kfp.Client.delete_pipeline_by_name = delete_pipeline_by_name
kfp.Client.delete_experiment_by_name = delete_experiment_by_name
kfp.Client.delete_run_by_name = delete_run_by_name
kfp.Client.delete_runs_by_experiment = delete_runs_by_experiment
kfp.Client.upload_pipeline_version = upload_pipeline_version
kfp.dsl.NotebookOp = NotebookOp
kfp.dsl.PythonFileOp = PythonFileOp
kfp.components.load_component_from_gcs = load_component_from_gcs
kfp.components.CloudComponentStore = CloudComponentStore
