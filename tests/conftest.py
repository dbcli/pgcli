import pytest
from utils import (POSTGRES_HOST, POSTGRES_USER, create_db, db_connection,
                   drop_tables)
import pgcli.pgexecute


@pytest.yield_fixture(scope="function")
def connection():
    create_db('_test_db')
    connection = db_connection('_test_db')
    yield connection

    drop_tables(connection)
    connection.close()


@pytest.fixture
def cursor(connection):
    with connection.cursor() as cur:
        return cur


@pytest.fixture
def executor(connection):
    return pgcli.pgexecute.PGExecute(database='_test_db', user=POSTGRES_USER,
            host=POSTGRES_HOST, password=None, port=None, dsn=None)


@pytest.fixture
def exception_formatter():
    return lambda e: str(e)


