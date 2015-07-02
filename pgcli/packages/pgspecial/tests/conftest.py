import pytest
from dbutils import (create_db, db_connection, setup_db, teardown_db)
from pgcli.packages.pgspecial import PGSpecial


@pytest.yield_fixture(scope='module')
def connection():
    create_db('_test_db')
    connection = db_connection('_test_db')
    setup_db(connection)
    yield connection

    teardown_db(connection)
    connection.close()


@pytest.fixture
def cursor(connection):
    with connection.cursor() as cur:
        return cur


@pytest.fixture
def executor(connection):
    cur = connection.cursor()
    pgspecial = PGSpecial()

    def query_runner(sql):
        results = []
        for title, rows, headers, status in pgspecial.execute(cur=cur, sql=sql):
            results.extend((title, list(rows), headers, status))
        return results
    return query_runner
