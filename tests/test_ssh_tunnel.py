import os
from unittest.mock import patch, MagicMock, ANY

import pytest
from configobj import ConfigObj
from click.testing import CliRunner
from sshtunnel import SSHTunnelForwarder

from pgcli.main import cli, notify_callback, PGCli
from pgcli.pgexecute import PGExecute


@pytest.fixture
def mock_ssh_tunnel_forwarder() -> MagicMock:
    mock_ssh_tunnel_forwarder = MagicMock(SSHTunnelForwarder, local_bind_ports=[1111], autospec=True)
    with patch(
        "pgcli.main.sshtunnel.SSHTunnelForwarder",
        return_value=mock_ssh_tunnel_forwarder,
    ) as mock:
        yield mock


@pytest.fixture
def mock_pgexecute() -> MagicMock:
    with patch.object(PGExecute, "__init__", return_value=None) as mock_pgexecute:
        yield mock_pgexecute


def test_ssh_tunnel(mock_ssh_tunnel_forwarder: MagicMock, mock_pgexecute: MagicMock) -> None:
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

    call_args, call_kwargs = mock_pgexecute.call_args
    # Original host is preserved for .pgpass lookup, hostaddr has tunnel endpoint
    assert call_args[0] == db_params["database"]  # database
    assert call_args[1] == db_params["user"]  # user
    assert call_args[2] == db_params["passwd"]  # passwd
    assert call_args[3] == db_params["host"]  # original host preserved
    assert call_args[4] == pgcli.ssh_tunnel.local_bind_ports[0]  # tunnel port
    assert call_kwargs.get("hostaddr") == "127.0.0.1"  # tunnel endpoint via hostaddr
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

    call_args, call_kwargs = mock_pgexecute.call_args
    # Original host is preserved, hostaddr has tunnel endpoint
    assert call_args[3] == db_params["host"]  # original host preserved
    assert call_args[4] == pgcli.ssh_tunnel.local_bind_ports[0]  # tunnel port
    assert call_kwargs.get("hostaddr") == "127.0.0.1"
    mock_ssh_tunnel_forwarder.reset_mock()
    mock_pgexecute.reset_mock()

    # Test with DSN
    dsn = f"user={db_params['user']} password={db_params['passwd']} host={db_params['host']} port={db_params['port']}"

    pgcli = PGCli(ssh_tunnel_url=tunnel_url)
    pgcli.connect(dsn=dsn)

    mock_ssh_tunnel_forwarder.assert_called_once_with(**expected_tunnel_params)
    mock_pgexecute.assert_called_once()

    call_args, call_kwargs = mock_pgexecute.call_args
    # DSN should contain original host AND hostaddr for tunnel
    dsn_arg = call_args[5]  # dsn is 6th positional arg
    assert f"host={db_params['host']}" in dsn_arg
    assert "hostaddr=127.0.0.1" in dsn_arg
    assert f"port={pgcli.ssh_tunnel.local_bind_ports[0]}" in dsn_arg


def test_ssh_tunnel_preserves_original_host_for_pgpass(
    mock_ssh_tunnel_forwarder: MagicMock, mock_pgexecute: MagicMock
) -> None:
    """Verify that the original hostname is preserved for .pgpass lookup."""
    tunnel_url = "bastion.example.com"
    original_host = "production.db.example.com"

    pgcli = PGCli(ssh_tunnel_url=tunnel_url)
    pgcli.connect(database="mydb", host=original_host, user="dbuser", passwd="dbpass")

    call_args, call_kwargs = mock_pgexecute.call_args
    # host parameter should be the original, not 127.0.0.1
    assert call_args[3] == original_host
    # hostaddr should be the tunnel endpoint
    assert call_kwargs.get("hostaddr") == "127.0.0.1"


def test_ssh_tunnel_with_dsn_preserves_host(
    mock_ssh_tunnel_forwarder: MagicMock, mock_pgexecute: MagicMock
) -> None:
    """DSN connections should include hostaddr for tunnel while preserving host."""
    tunnel_url = "bastion.example.com"
    dsn = "host=production.db.example.com port=5432 dbname=mydb user=dbuser"

    pgcli = PGCli(ssh_tunnel_url=tunnel_url)
    pgcli.connect(dsn=dsn)

    call_args, call_kwargs = mock_pgexecute.call_args
    dsn_arg = call_args[5]
    assert "host=production.db.example.com" in dsn_arg
    assert "hostaddr=127.0.0.1" in dsn_arg


def test_no_ssh_tunnel_does_not_set_hostaddr(mock_pgexecute: MagicMock) -> None:
    """Without SSH tunnel, hostaddr should not be set."""
    pgcli = PGCli()
    pgcli.connect(database="mydb", host="localhost", user="user", passwd="pass")

    call_args, call_kwargs = mock_pgexecute.call_args
    assert "hostaddr" not in call_kwargs


def test_connect_uri_without_ssh_tunnel(mock_pgexecute: MagicMock) -> None:
    """connect_uri should work normally without SSH tunnel."""
    pgcli = PGCli()
    pgcli.connect_uri("postgresql://user:pass@localhost/mydb")

    mock_pgexecute.assert_called_once()
    call_args, call_kwargs = mock_pgexecute.call_args
    assert "hostaddr" not in call_kwargs


def test_connect_uri_passes_dsn(mock_pgexecute: MagicMock) -> None:
    """connect_uri should pass the URI as dsn parameter."""
    uri = "postgresql://user:pass@localhost/mydb"
    pgcli = PGCli()
    pgcli.connect_uri(uri)

    call_args, call_kwargs = mock_pgexecute.call_args
    # dsn is passed as the 6th positional arg to PGExecute.__init__
    assert call_args[5] == uri


def test_cli_with_tunnel() -> None:
    runner = CliRunner()
    tunnel_url = "mytunnel"
    with patch.object(PGCli, "__init__", autospec=True, return_value=None) as mock_pgcli:
        runner.invoke(cli, ["--ssh-tunnel", tunnel_url])
        mock_pgcli.assert_called_once()
        call_args, call_kwargs = mock_pgcli.call_args
        assert call_kwargs["ssh_tunnel_url"] == tunnel_url


def test_config(tmpdir: os.PathLike, mock_ssh_tunnel_forwarder: MagicMock, mock_pgexecute: MagicMock) -> None:
    pgclirc = str(tmpdir.join("rcfile"))

    tunnel_user = "tunnel_user"
    tunnel_passwd = "tunnel_pass"
    tunnel_host = "tunnel.host"
    tunnel_port = 1022
    tunnel_url = f"{tunnel_user}:{tunnel_passwd}@{tunnel_host}:{tunnel_port}"

    tunnel2_url = "tunnel2.host"

    config = ConfigObj()
    config.filename = pgclirc
    config["ssh tunnels"] = {}
    config["ssh tunnels"][r"\.com$"] = tunnel_url
    config["ssh tunnels"][r"^hello-"] = tunnel2_url
    config.write()

    # Unmatched host
    pgcli = PGCli(pgclirc_file=pgclirc)
    pgcli.connect(host="unmatched.host")
    mock_ssh_tunnel_forwarder.assert_not_called()

    # Host matching first tunnel
    pgcli = PGCli(pgclirc_file=pgclirc)
    pgcli.connect(host="matched.host.com")
    mock_ssh_tunnel_forwarder.assert_called_once()
    call_args, call_kwargs = mock_ssh_tunnel_forwarder.call_args
    assert call_kwargs["ssh_address_or_host"] == (tunnel_host, tunnel_port)
    assert call_kwargs["ssh_username"] == tunnel_user
    assert call_kwargs["ssh_password"] == tunnel_passwd
    mock_ssh_tunnel_forwarder.reset_mock()

    # Host matching second tunnel
    pgcli = PGCli(pgclirc_file=pgclirc)
    pgcli.connect(host="hello-i-am-matched")
    mock_ssh_tunnel_forwarder.assert_called_once()

    call_args, call_kwargs = mock_ssh_tunnel_forwarder.call_args
    assert call_kwargs["ssh_address_or_host"] == (tunnel2_url, 22)
    mock_ssh_tunnel_forwarder.reset_mock()

    # Host matching both tunnels (will use the first one matched)
    pgcli = PGCli(pgclirc_file=pgclirc)
    pgcli.connect(host="hello-i-am-matched.com")
    mock_ssh_tunnel_forwarder.assert_called_once()

    call_args, call_kwargs = mock_ssh_tunnel_forwarder.call_args
    assert call_kwargs["ssh_address_or_host"] == (tunnel_host, tunnel_port)
    assert call_kwargs["ssh_username"] == tunnel_user
    assert call_kwargs["ssh_password"] == tunnel_passwd
