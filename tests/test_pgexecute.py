# coding=UTF-8

import pytest
import psycopg2
from textwrap import dedent
from utils import run, dbtest

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
def test_bools_are_treated_as_strings(executor):
    run(executor, '''create table test(a boolean)''')
    run(executor, '''insert into test values(True)''')
    assert run(executor, '''select * from test''', join=True) == dedent("""\
        +------+
        | a    |
        |------|
        | True |
        +------+
        SELECT 1""")

@dbtest
def test_schemata_table_and_columns_query(executor):
    run(executor, "create table a(x text, y text)")
    run(executor, "create table b(z text)")
    run(executor, "create schema schema1")
    run(executor, "create table schema1.c (w text)")
    run(executor, "create schema schema2")

    assert executor.schemata() == ['public', 'schema1', 'schema2']
    assert executor.tables() == [
        ('public', 'a'), ('public', 'b'), ('schema1', 'c')]

    assert executor.columns() == [
        ('public', 'a', 'x'), ('public', 'a', 'y'),
        ('public', 'b', 'z'), ('schema1', 'c', 'w')]

    assert executor.search_path() == ['public']

@dbtest
def test_functions_query(executor):
    run(executor, '''create function func1() returns int
                     language sql as $$select 1$$''')
    run(executor, 'create schema schema1')
    run(executor, '''create function schema1.func2() returns int
                     language sql as $$select 2$$''')

    funcs = list(executor.functions())
    assert funcs == [('public', 'func1'), ('schema1', 'func2')]

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
    assert len(result) == 4  # 2 * (output+status)
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


@dbtest
def test_bytea_field_support_in_output(executor):
    run(executor, "create table binarydata(c bytea)")
    run(executor,
        "insert into binarydata (c) values (decode('DEADBEEF', 'hex'))")

    assert u'\\xdeadbeef' in run(executor, "select * from binarydata", join=True)

@dbtest
def test_unicode_support_in_unknown_type(executor):
    assert u'日本語' in run(executor, "SELECT '日本語' AS japanese;", join=True)
