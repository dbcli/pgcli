import os
from contextlib import ExitStack
from unittest import mock

import pytest
import click
from click.testing import CliRunner
from configobj import ConfigObj
from psycopg.conninfo import conninfo_to_dict

from pgcli.main import PGCli, cli, read_env_database, setproctitle


URL = "postgresql://file_user:secret@file_host:6543/file_db?sslmode=require"
STOP = RuntimeError("connection selected")


@pytest.fixture
def invoke(tmp_path, monkeypatch):
    # setproctitle locates argv using the original environment on Linux.
    # Initialize it before removing connection variables from that environment.
    if setproctitle:
        setproctitle.getproctitle()
    for name in tuple(os.environ):
        if name.startswith("PG") or name in ("DSN", "DATABASE_URL", "DATABASE_URI", "DB_URL", "DB_URI"):
            monkeypatch.delenv(name)
    monkeypatch.chdir(tmp_path)
    config = tmp_path / "pgclirc"
    config.write_text("[main]\n[alias_dsn]\nlocal = postgres://alias_host/alias_db\n", encoding="utf-8")

    def run(args):
        with ExitStack() as stack:
            connections = {
                name: stack.enter_context(mock.patch.object(PGCli, name, side_effect=STOP))
                for name in ("connect_uri", "connect_dsn", "connect_service", "connect")
            }
            result = CliRunner().invoke(cli, ["--pgclirc", str(config), *args])
        return result, connections

    return run


def assert_connection(result, connections, method, *args, **kwargs):
    assert result.exception is STOP, result.output
    connections[method].assert_called_once_with(*args, **kwargs)
    assert sum(connection.call_count for connection in connections.values()) == 1


@pytest.mark.parametrize("name", ["DATABASE_URL", "DATABASE_URI", "DB_URL", "DB_URI"])
@pytest.mark.parametrize("filename", [".env", ".env.local"])
def test_env_file_url(invoke, tmp_path, name, filename):
    env_file = tmp_path / filename
    env_file.write_text(f"# project settings\nexport {name}='{URL}'\n", encoding="utf-8-sig")
    result, connections = invoke(["--env-file", str(env_file)])
    assert_connection(result, connections, "connect_uri", URL)


def test_env_file_variable_precedence(invoke, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DB_URI=postgres://fourth/db\nDB_URL=postgres://third/db\nDATABASE_URI=postgres://second/db\nDATABASE_URL=postgres://first/db\n",
        encoding="utf-8",
    )
    result, connections = invoke(["--env-file", str(env_file)])
    assert_connection(result, connections, "connect_uri", "postgres://first/db")


def test_env_file_skips_empty_variables(invoke, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(f"DATABASE_URL\nDATABASE_URI=\nDB_URL='  '\nDB_URI={URL}\n", encoding="utf-8")
    result, connections = invoke(["--env-file", str(env_file)])
    assert_connection(result, connections, "connect_uri", URL)


def test_env_file_overrides_environment_defaults(invoke, tmp_path, monkeypatch):
    for name, value in {
        "PGDATABASE": "environment_db",
        "PGHOST": "environment_host",
        "PGPORT": "9876",
        "PGUSER": "environment_user",
        "PGSERVICE": "environment_service",
        "DSN": "environment_alias",
        "DATABASE_URL": "postgres://environment/db",
    }.items():
        monkeypatch.setenv(name, value)
    env_file = tmp_path / ".env"
    env_file.write_text(f"DB_URL={URL}\nPGPASSWORD=not_exported\nUNRELATED=not_exported\n", encoding="utf-8")
    before = dict(os.environ)
    result, connections = invoke(["--env-file", str(env_file)])
    assert_connection(result, connections, "connect_uri", URL)
    for name in (*before, "PGPASSWORD", "UNRELATED"):
        # PGCli itself sets PAGER/LESS during initialization.
        if name not in ("PAGER", "LESS"):
            assert os.environ.get(name) == before.get(name)


@pytest.mark.parametrize(
    "args, method, expected, kwargs",
    [
        (["explicit_db"], "connect", ("explicit_db", "", None, 5432), {}),
        (["-d", "explicit_db"], "connect", ("explicit_db", "", None, 5432), {}),
        (["explicit_db", "explicit_user"], "connect", ("explicit_db", "", "explicit_user", 5432), {}),
        (["-h", "explicit_host"], "connect", ("", "explicit_host", None, 5432), {}),
        (["-p", "7654"], "connect", ("", "", None, 7654), {}),
        (["-U", "explicit_user"], "connect", ("", "", "explicit_user", 5432), {}),
        (["-u", "explicit_user"], "connect", ("", "", "explicit_user", 5432), {}),
        (["-D", "local"], "connect_uri", ("postgres://alias_host/alias_db",), {}),
        (["postgres://explicit/db"], "connect_uri", ("postgres://explicit/db",), {}),
        (["host=explicit dbname=db"], "connect_dsn", ("host=explicit dbname=db",), {"user": None}),
        (["service=explicit"], "connect_service", ("explicit", None), {}),
    ],
)
def test_explicit_connection_takes_precedence(invoke, tmp_path, args, method, expected, kwargs):
    env_file = tmp_path / ".env"
    env_file.write_text(f"DB_URL={URL}\n", encoding="utf-8")
    result, connections = invoke(["--env-file", str(env_file), *args])
    assert_connection(result, connections, method, *expected, **kwargs)


def test_env_file_is_opt_in(invoke, tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(f"DB_URL={URL}\n", encoding="utf-8")
    monkeypatch.setenv("DB_URL", URL)
    result, connections = invoke([])
    assert_connection(result, connections, "connect", "", "", None, 5432)


@pytest.mark.parametrize("option", ["--ping", "--list"])
def test_env_file_with_connection_checks(invoke, tmp_path, option):
    env_file = tmp_path / ".env"
    env_file.write_text(f"DB_URL={URL}\n", encoding="utf-8")
    result, connections = invoke(["--env-file", str(env_file), option])
    assert_connection(result, connections, "connect_uri", URL)


def test_env_file_list_without_database(invoke, tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("DB_URL=postgres://user@host:6543?sslmode=require\n", encoding="utf-8")
    result, connections = invoke(["--env-file", str(env_file), "--list"])
    assert result.exception is STOP, result.output
    assert conninfo_to_dict(connections["connect_dsn"].call_args.args[0]) == {
        "user": "user",
        "host": "host",
        "port": "6543",
        "dbname": "postgres",
        "sslmode": "require",
    }


@pytest.mark.parametrize(
    "contents, message",
    [
        ("", "No non-empty"),
        ("UNRELATED=value\n", "No non-empty"),
        ("DB_URL=\n", "No non-empty"),
        ("DB_URL=mysql://user:secret@host/db\n", "must be a PostgreSQL URL"),
        ("DB_URL=postgres://user:secret@host/db?unknown_parameter=secret\n", "invalid PostgreSQL URL"),
        (b"DB_URL=\xff", "Could not read"),
    ],
)
def test_env_file_errors(invoke, tmp_path, contents, message):
    env_file = tmp_path / ".env"
    env_file.write_bytes(contents if isinstance(contents, bytes) else contents.encode("utf-8"))
    result, connections = invoke(["--env-file", str(env_file)])
    assert result.exit_code == 2
    assert message in result.output
    assert "secret" not in result.output
    assert not any(connection.called for connection in connections.values())


@pytest.mark.parametrize("filename", ["missing", "."])
def test_env_file_path_errors(invoke, filename):
    result, connections = invoke(["--env-file", filename])
    assert result.exit_code == 2
    assert "--env-file" in result.output
    assert not any(connection.called for connection in connections.values())


def test_env_file_read_error():
    with mock.patch("pgcli.main.open", side_effect=PermissionError), pytest.raises(click.BadParameter, match="Could not read"):
        read_env_database(".env")


def test_env_file_does_not_interpolate(invoke, tmp_path, monkeypatch):
    monkeypatch.setenv("PASSWORD", "expanded")
    url = "postgres://user:${PASSWORD}@host/db"
    env_file = tmp_path / ".env"
    env_file.write_text(f"DB_URL='{url}'\n", encoding="utf-8")
    result, connections = invoke(["--env-file", str(env_file)])
    assert_connection(result, connections, "connect_uri", url)


def test_env_file_url_is_not_logged(invoke, tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(f"DB_URL={URL}\n", encoding="utf-8")
    monkeypatch.setattr("pgcli.main.setproctitle", None)
    with mock.patch("pgcli.main.PGCli") as pgcli:
        instance = pgcli.return_value
        instance.config = ConfigObj({"main": {"use_local_timezone": "False"}})
        result = CliRunner().invoke(cli, ["--env-file", str(env_file)])
    assert result.exit_code == 0, result.output
    instance.connect_uri.assert_called_once_with(URL)
    instance.run_cli.assert_called_once()
    instance.logger.debug.assert_called_once()
    assert URL not in str(instance.logger.debug.call_args)
    assert "<from --env-file>" in str(instance.logger.debug.call_args)
