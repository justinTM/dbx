import datetime as dt
import unittest
from unittest.mock import patch

from mlflow import ActiveRun
from mlflow.entities import Experiment
from mlflow.entities.run import Run, RunInfo, RunData

from dbx.commands.configure import configure
from dbx.commands.execute import execute
from .utils import DbxTest, invoke_cli_runner, test_dbx_config

run_info = RunInfo(
    run_uuid="1",
    experiment_id="1",
    user_id="dbx",
    status="STATUS",
    start_time=dt.datetime.now(),
    end_time=dt.datetime.now(),
    lifecycle_stage="STAGE",
    artifact_uri="dbfs:/dbx.unique.uri"
)
run_data = RunData()
run_mock = ActiveRun(Run(run_info, run_data))


class ExecuteTest(DbxTest):
    @patch("databricks_cli.configure.provider.ProfileConfigProvider.get_config",
           return_value=test_dbx_config)
    @patch("databricks_cli.workspace.api.WorkspaceService.mkdirs", return_value=True)
    @patch("databricks_cli.clusters.api.ClusterService.get_cluster",
           return_value={"cluster_name": "some-name", "state": "RUNNING"})
    @patch("mlflow.get_experiment_by_name", return_value=Experiment("id", None, "location", None, None))
    @patch("dbx.utils.common.ApiV1Client.create_context", return_value={"id": 1})
    @patch("dbx.utils.common.ApiV1Client.execute_command", return_value={"id": 1})
    @patch("dbx.utils.common.ApiV1Client.get_command_status",
           return_value={"status": "Finished", "results": {"resultType": "Ok", "data": "Ok!"}})
    @patch("mlflow.start_run", return_value=run_mock)
    @patch("mlflow.log_artifact", return_value=None)
    @patch("mlflow.set_tags", return_value=None)
    @patch("mlflow.get_experiment_by_name", return_value=Experiment("id", None, "location", None, None))
    @patch("mlflow.set_experiment", return_value=None)
    def test_execute(self, *args):
        with self.project_dir:
            ws_dir = "/Shared/dbx/projects/%s" % self.project_name
            configure_result = invoke_cli_runner(configure, [
                "--environment", "test",
                "--profile", self.profile_name,
                "--workspace-dir", ws_dir
            ])
            self.assertEqual(configure_result.exit_code, 0)

            execute_result = invoke_cli_runner(execute, [
                "--environment", "default",
                "--cluster-id", "000-some-cluster-id",
                "--job", f"{self.project_name}-sample"
            ])

            self.assertEqual(execute_result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()