from unittest.mock import patch

from click.testing import CliRunner

from pgcli.main import PGCli, cli


def test_dsn_override(tmpdir):
    old_dsn = "postgresql://old_user:password@old_host:5432/old_db"
    new_host = "new_host"
    new_port = 5555
    new_user = "new_user"
    new_dbname = "new_db"

    pgclirc = tmpdir.join("rcfile")
    pgclirc.write(f"[alias_dsn]\ndsn = {old_dsn}")

    with patch.object(
        PGCli, "connect_uri", autospec=True, return_value=None
    ) as mock_connect_uri:
        CliRunner().invoke(
            cli,
            [
                "--pgclirc", str(pgclirc),
                "-D", "dsn",
                "-h", new_host,
                "-p", new_port,
                "-u", new_user,
                "-d", new_dbname,
                "-W",
            ],
        )

        mock_connect_uri.assert_called_once()
        args, kwargs = mock_connect_uri.call_args
        assert args[1] == old_dsn
        assert kwargs["host"] == new_host
        assert kwargs["port"] == new_port
        assert kwargs["user"] == new_user
        assert kwargs["dbname"] == new_dbname
        assert kwargs["password"] == ""
