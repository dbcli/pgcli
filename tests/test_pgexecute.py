# coding=UTF-8

import pytest
import psycopg2
from textwrap import dedent
from utils import run, dbtest, requires_json, requires_jsonb

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
def test_schemata_table_views_and_columns_query(executor):
    run(executor, "create table a(x text, y text)")
    run(executor, "create table b(z text)")
    run(executor, "create view d as select 1 as e")
    run(executor, "create schema schema1")
    run(executor, "create table schema1.c (w text)")
    run(executor, "create schema schema2")

    # schemata
    # don't enforce all members of the schemas since they may include postgres
    # temporary schemas
    assert set(executor.schemata()) >= set([
        'public', 'pg_catalog', 'information_schema', 'schema1', 'schema2'])
    assert executor.search_path() == ['pg_catalog', 'public']

    # tables
    assert set(executor.tables()) >= set([
        ('public', 'a'), ('public', 'b'), ('schema1', 'c')])

    assert set(executor.table_columns()) >= set([
        ('public', 'a', 'x'), ('public', 'a', 'y'),
        ('public', 'b', 'z'), ('schema1', 'c', 'w')])

    # views
    assert set(executor.views()) >= set([
        ('public', 'd')])

    assert set(executor.view_columns()) >= set([
        ('public', 'd', 'e')])

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
def test_multiple_queries_with_special_command_same_line(executor):
    result = run(executor, "select 'foo'; \d")
    assert len(result) == 4  # 2 * (output+status)
    assert "foo" in result[0]
    # This is a lame check. :(
    assert "Schema" in result[2]

@dbtest
def test_multiple_queries_same_line_syntaxerror(executor):
    with pytest.raises(psycopg2.ProgrammingError) as excinfo:
        run(executor, "select 'foo'; invalid syntax")
    assert 'syntax error at or near "invalid"' in str(excinfo.value)

@dbtest
def test_special_command_help(executor):
    result = run(executor, '\\?')[0].split('|')
    assert(result[1].find(u'Command') != -1)
    assert(result[2].find(u'Description') != -1)


@dbtest
def test_bytea_field_support_in_output(executor):
    run(executor, "create table binarydata(c bytea)")
    run(executor,
        "insert into binarydata (c) values (decode('DEADBEEF', 'hex'))")

    assert u'\\xdeadbeef' in run(executor, "select * from binarydata", join=True)


@dbtest
def test_unicode_support_in_unknown_type(executor):
    assert u'日本語' in run(executor, "SELECT '日本語' AS japanese;", join=True)


@requires_json
def test_json_renders_without_u_prefix(executor, expanded):
    run(executor, "create table jsontest(d json)")
    run(executor, """insert into jsontest (d) values ('{"name": "Éowyn"}')""")
    result = run(executor, "SELECT d FROM jsontest LIMIT 1", join=True)

    assert u'{"name": "Éowyn"}' in result


@requires_jsonb
def test_jsonb_renders_without_u_prefix(executor, expanded):
    run(executor, "create table jsonbtest(d jsonb)")
    run(executor, """insert into jsonbtest (d) values ('{"name": "Éowyn"}')""")
    result = run(executor, "SELECT d FROM jsonbtest LIMIT 1", join=True)

    assert u'{"name": "Éowyn"}' in result


@dbtest
@pytest.mark.parametrize('value', ['10000000', '10000000.0', '10000000000000'])
def test_large_numbers_render_directly(executor, value):
    run(executor, "create table numbertest(a numeric)")
    run(executor,
        "insert into numbertest (a) values ({0})".format(value))

    assert value in run(executor, "select * from numbertest", join=True)
