import pytest
from utils import *
from pgcli.pgexecute import PGExecute


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
    return PGExecute(database='_test_db', user=POSTGRES_USER, host=POSTGRES_HOST,
        password=None, port=None)
