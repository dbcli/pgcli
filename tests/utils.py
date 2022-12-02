import pytest
import psycopg
from pgcli.main import emit_output, OutputSettings
from os import getenv
from unittest.mock import Mock

POSTGRES_USER = getenv("PGUSER", "postgres")
POSTGRES_HOST = getenv("PGHOST", "localhost")
POSTGRES_PORT = getenv("PGPORT", 5432)
POSTGRES_PASSWORD = getenv("PGPASSWORD", "postgres")


def db_connection(dbname=None):
    conn = psycopg.connect(
        user=POSTGRES_USER,
        host=POSTGRES_HOST,
        password=POSTGRES_PASSWORD,
        port=POSTGRES_PORT,
        dbname=dbname,
    )
    conn.autocommit = True
    return conn


try:
    conn = db_connection()
    CAN_CONNECT_TO_DB = True
    SERVER_VERSION = conn.info.parameter_status("server_version")
    JSON_AVAILABLE = True
    JSONB_AVAILABLE = True
except Exception as x:
    CAN_CONNECT_TO_DB = JSON_AVAILABLE = JSONB_AVAILABLE = False
    SERVER_VERSION = 0


dbtest = pytest.mark.skipif(
    not CAN_CONNECT_TO_DB,
    reason="Need a postgres instance at localhost accessible by user 'postgres'",
)


requires_json = pytest.mark.skipif(
    not JSON_AVAILABLE, reason="Postgres server unavailable or json type not defined"
)


requires_jsonb = pytest.mark.skipif(
    not JSONB_AVAILABLE, reason="Postgres server unavailable or jsonb type not defined"
)


def create_db(dbname):
    with db_connection().cursor() as cur:
        try:
            cur.execute("""CREATE DATABASE _test_db""")
        except:
            pass


def drop_tables(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            DROP SCHEMA public CASCADE;
            CREATE SCHEMA public;
            DROP SCHEMA IF EXISTS schema1 CASCADE;
            DROP SCHEMA IF EXISTS schema2 CASCADE"""
        )


def run(
    executor, sql, join=False, expanded=False, pgspecial=None, exception_formatter=None
):
    "Return string output for the sql to be run"

    results = executor.run(sql, pgspecial, exception_formatter)
    formatted = []
    settings = OutputSettings(
        table_format="psql", dcmlfmt="d", floatfmt="g", expanded=expanded
    )
    cli = Mock()
    for title, rows, headers, status, sql, success, is_special in results:
        emit_output(cli, "", title, rows, headers, status, settings)

    if cli.pager_output.emit.called:
        formatted.extend([c.args[1] for c in cli.pager_output.emit.call_args_list])
    if cli.stdout_output.emit.called:
        formatted.extend([c.args[1] for c in cli.stdout_output.emit.call_args_list])

    if join:
        formatted = "\n".join(formatted)

    return formatted


def completions_to_set(completions):
    return {
        (completion.display_text, completion.display_meta_text)
        for completion in completions
    }
