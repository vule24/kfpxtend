import kfp
from ._client import *
from ._operators import *
from ._component_store import *
from ._components import *
from ._auth import *
from ._pipeline import *

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

kfp.compiler.Compiler.__create_pipeline_workflow = kfp.compiler.Compiler._create_pipeline_workflow
kfp.compiler.Compiler._create_pipeline_workflow = create_pipeline_workflow
kfp.dsl.PipelineConf.gcp_sa_name = None
kfp.dsl.PipelineConf.set_gcp_sa = set_gcp_sa