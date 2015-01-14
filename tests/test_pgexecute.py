# coding=UTF-8

from pgcli.pgexecute import _parse_dsn
from textwrap import dedent
from utils import *

def test__parse_dsn():
    test_cases = [
            # Full dsn with all components.
            ('postgres://user:password@host:5432/dbname',
                ('dbname', 'user', 'password', 'host', '5432')),

            # dsn without password.
            ('postgres://user@host:5432/dbname',
                ('dbname', 'user', 'fpasswd', 'host', '5432')),

            # dsn without user or password.
            ('postgres://localhost:5432/dbname',
                ('dbname', 'fuser', 'fpasswd', 'localhost', '5432')),

            # dsn without port.
            ('postgres://user:password@host/dbname',
                ('dbname', 'user', 'password', 'host', '1234')),

            # dsn without password and port.
            ('postgres://user@host/dbname',
                ('dbname', 'user', 'fpasswd', 'host', '1234')),

            # dsn without user, password, port.
            ('postgres://localhost/dbname',
                ('dbname', 'fuser', 'fpasswd', 'localhost', '1234')),

            # dsn without user, password, port or host.
            ('postgres:///dbname',
                ('dbname', 'fuser', 'fpasswd', 'fhost', '1234')),

            # Full dsn with all components but with postgresql:// prefix.
            ('postgresql://user:password@host:5432/dbname',
                ('dbname', 'user', 'password', 'host', '5432')),
            ]

    for dsn, expected in test_cases:
        assert _parse_dsn(dsn, 'fuser', 'fpasswd', 'fhost', '1234') == expected

@dbtest
def test_conn(executor):
    run(executor, '''create table test(a text)''')
    run(executor, '''insert into test values('abc')''')
    assert run(executor, '''select * from test''', join=True) == dedent("""\
        +-----+
        | a   |
        |-----|
        | abc |
        +-----+
        SELECT 1""")

@dbtest
def test_table_and_columns_query(executor):
    run(executor, "create table a(x text, y text)")
    run(executor, "create table b(z text)")

    tables, columns = executor.tables()
    assert tables == ['a', 'b']
    assert columns['a'] == ['x', 'y']
    assert columns['b'] == ['z']

@dbtest
def test_database_list(executor):
    databases = executor.databases()
    assert '_test_db' in databases

@dbtest
def test_invalid_syntax(executor):
    with pytest.raises(psycopg2.ProgrammingError) as excinfo:
        run(executor, 'invalid syntax!')
    assert 'syntax error at or near "invalid"' in str(excinfo.value)

@dbtest
def test_invalid_column_name(executor):
    with pytest.raises(psycopg2.ProgrammingError) as excinfo:
        run(executor, 'select invalid command')
    assert 'column "invalid" does not exist' in str(excinfo.value)

@pytest.yield_fixture(params=[True, False])
def expanded(request, executor):
    if request.param:
        run(executor, '\\x')
    yield request.param
    if request.param:
        run(executor, '\\x')

@dbtest
def test_unicode_support_in_output(executor, expanded):
    run(executor, "create table unicodechars(t text)")
    run(executor, "insert into unicodechars (t) values ('é')")

    # See issue #24, this raises an exception without proper handling
    assert u'é' in run(executor, "select * from unicodechars", join=True)

@dbtest
def test_multiple_queries_same_line(executor):
    result = run(executor, "select 'foo'; select 'bar'")
    assert len(result) == 4 # 2 * (output+status)
    assert "foo" in result[0]
    assert "bar" in result[2]

@dbtest
def test_multiple_queries_same_line_syntaxerror(executor):
    with pytest.raises(psycopg2.ProgrammingError) as excinfo:
        run(executor, "select 'foo'; invalid syntax")
    assert 'syntax error at or near "invalid"' in str(excinfo.value)

@dbtest
def test_special_command(executor):
    run(executor, '\\?')