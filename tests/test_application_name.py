from unittest.mock import patch

from click.testing import CliRunner

from pgcli.main import cli
from pgcli.pgexecute import PGExecute


def test_application_name_in_env():
    runner = CliRunner()
    app_name = "wonderful_app"
    with patch.object(PGExecute, "__init__") as mock_pgxecute:
        runner.invoke(cli, ["127.0.0.1:5432/hello", "user"], env={"PGAPPNAME": app_name})
        kwargs = mock_pgxecute.call_args.kwargs
        assert kwargs.get("application_name") == app_name
