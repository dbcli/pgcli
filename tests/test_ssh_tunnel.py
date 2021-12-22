from unittest.mock import patch, MagicMock, ANY

import pytest
from click.testing import CliRunner
from sshtunnel import SSHTunnelForwarder

from pgcli.main import cli, PGCli
from pgcli.pgexecute import PGExecute


@pytest.fixture
def mock_ssh_tunnel_forwarder() -> MagicMock:
    mock_ssh_tunnel_forwarder = MagicMock(
        SSHTunnelForwarder, local_bind_ports=[1111], autospec=True
    )
    with patch(
        "pgcli.main.sshtunnel.SSHTunnelForwarder",
        return_value=mock_ssh_tunnel_forwarder,
    ) as mock:
        yield mock


@pytest.fixture
def mock_pgexecute() -> MagicMock:
    with patch.object(PGExecute, "__init__", return_value=None) as mock_pgexecute:
        yield mock_pgexecute


def test_ssh_tunnel(
    mock_ssh_tunnel_forwarder: MagicMock, mock_pgexecute: MagicMock
) -> None:
    # Test with just a host
    tunnel_url = "some.host"
    db_params = {
        "database": "dbname",
        "host": "db.host",
        "user": "db_user",
        "passwd": "db_passwd",
    }
    expected_tunnel_params = {
        "local_bind_address": ("127.0.0.1",),
        "remote_bind_address": (db_params["host"], 5432),
        "ssh_address_or_host": (tunnel_url, 22),
        "logger": ANY,
    }

    pgcli = PGCli(ssh_tunnel_url=tunnel_url)
    pgcli.connect(**db_params)

    mock_ssh_tunnel_forwarder.assert_called_once_with(**expected_tunnel_params)
    mock_ssh_tunnel_forwarder.return_value.start.assert_called_once()
    mock_pgexecute.assert_called_once()
    assert mock_pgexecute.call_args.args == (
        db_params["database"],
        db_params["user"],
        db_params["passwd"],
        "127.0.0.1",
        pgcli.ssh_tunnel.local_bind_ports[0],
        "",
    )
    mock_ssh_tunnel_forwarder.reset_mock()
    mock_pgexecute.reset_mock()

    # Test with a full url and with a specific db port
    tunnel_user = "tunnel_user"
    tunnel_passwd = "tunnel_pass"
    tunnel_host = "some.other.host"
    tunnel_port = 1022
    tunnel_url = f"ssh://{tunnel_user}:{tunnel_passwd}@{tunnel_host}:{tunnel_port}"
    db_params["port"] = 1234

    expected_tunnel_params["remote_bind_address"] = (
        db_params["host"],
        db_params["port"],
    )
    expected_tunnel_params["ssh_address_or_host"] = (tunnel_host, tunnel_port)
    expected_tunnel_params["ssh_username"] = tunnel_user
    expected_tunnel_params["ssh_password"] = tunnel_passwd

    pgcli = PGCli(ssh_tunnel_url=tunnel_url)
    pgcli.connect(**db_params)

    mock_ssh_tunnel_forwarder.assert_called_once_with(**expected_tunnel_params)
    mock_ssh_tunnel_forwarder.return_value.start.assert_called_once()
    mock_pgexecute.assert_called_once()
    assert mock_pgexecute.call_args.args == (
        db_params["database"],
        db_params["user"],
        db_params["passwd"],
        "127.0.0.1",
        pgcli.ssh_tunnel.local_bind_ports[0],
        "",
    )
    mock_ssh_tunnel_forwarder.reset_mock()
    mock_pgexecute.reset_mock()

    # Test with DSN
    dsn = (
        f"user={db_params['user']} password={db_params['passwd']} "
        f"host={db_params['host']} port={db_params['port']}"
    )

    pgcli = PGCli(ssh_tunnel_url=tunnel_url)
    pgcli.connect(dsn=dsn)

    expected_dsn = (
        f"user={db_params['user']} password={db_params['passwd']} "
        f"host=127.0.0.1 port={pgcli.ssh_tunnel.local_bind_ports[0]}"
    )

    mock_ssh_tunnel_forwarder.assert_called_once_with(**expected_tunnel_params)
    mock_pgexecute.assert_called_once()
    assert mock_pgexecute.call_args.args[5] == expected_dsn


def test_cli_with_tunnel() -> None:
    runner = CliRunner()
    tunnel_url = "mytunnel"
    with patch.object(
        PGCli, "__init__", autospec=True, return_value=None
    ) as mock_pgcli:
        runner.invoke(cli, ["--ssh-tunnel", tunnel_url])
        mock_pgcli.assert_called_once()
        assert mock_pgcli.call_args.kwargs["ssh_tunnel_url"] == tunnel_url
