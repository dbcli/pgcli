# coding=UTF-8

import pytest
import psycopg2
from pgspecial.main import PGSpecial
from pgcli.packages.parseutils.meta import FunctionMetadata
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
        ('public', 'a', 'x', 'text'), ('public', 'a', 'y', 'text'),
        ('public', 'b', 'z', 'text'), ('schema1', 'c', 'w', 'text')])

    # views
    assert set(executor.views()) >= set([
        ('public', 'd')])

    assert set(executor.view_columns()) >= set([
        ('public', 'd', 'e', 'integer')])

@dbtest
def test_foreign_key_query(executor):
    run(executor, "create schema schema1")
    run(executor, "create schema schema2")
    run(executor, "create table schema1.parent(parentid int PRIMARY KEY)")
    run(executor, "create table schema2.child(childid int PRIMARY KEY, motherid int REFERENCES schema1.parent)")

    assert set(executor.foreignkeys()) >= set([
        ('schema1', 'parent', 'parentid', 'schema2', 'child', 'motherid')])

@dbtest
def test_functions_query(executor):
    run(executor, '''create function func1() returns int
                     language sql as $$select 1$$''')
    run(executor, 'create schema schema1')
    run(executor, '''create function schema1.func2() returns int
                     language sql as $$select 2$$''')

    run(executor, '''create function func3()
                     returns table(x int, y int) language sql
                     as $$select 1, 2 from generate_series(1,5)$$;''')

    run(executor, '''create function func4(x int) returns setof int language sql
                     as $$select generate_series(1,5)$$;''')

    funcs = set(executor.functions())
    assert funcs >= set([
        FunctionMetadata('public', 'func1', None, [], [],
                         'integer', False, False, False),
        FunctionMetadata('public', 'func3', ['x', 'y'],
            ['integer', 'integer'], ['t', 't'], 'record', False, False, True),
        FunctionMetadata('public', 'func4', ('x',), ('integer',), [],
                         'integer', False, False, True),
        FunctionMetadata('schema1', 'func2', None, [], [],
                         'integer', False, False, False),
      ])


@dbtest
def test_datatypes_query(executor):
    run(executor, 'create type foo AS (a int, b text)')

    types = list(executor.datatypes())
    assert types == [('public', 'foo')]

@dbtest
def test_database_list(executor):
    databases = executor.databases()
    assert '_test_db' in databases

@dbtest
def test_invalid_syntax(executor, exception_formatter):
    result = run(executor, 'invalid syntax!',
                 exception_formatter=exception_formatter)
    assert 'syntax error at or near "invalid"' in result[0]

@dbtest
def test_invalid_column_name(executor, exception_formatter):
    result = run(executor, 'select invalid command',
                 exception_formatter=exception_formatter)
    assert 'column "invalid" does not exist' in result[0]


@pytest.fixture(params=[True, False])
def expanded(request):
    return request.param


@dbtest
def test_unicode_support_in_output(executor, expanded):
    run(executor, "create table unicodechars(t text)")
    run(executor, u"insert into unicodechars (t) values ('é')")

    # See issue #24, this raises an exception without proper handling
    assert u'é' in run(executor, "select * from unicodechars",
                       join=True, expanded=expanded)


@dbtest
def test_multiple_queries_same_line(executor):
    result = run(executor, "select 'foo'; select 'bar'")
    assert len(result) == 4  # 2 * (output+status)
    assert "foo" in result[0]
    assert "bar" in result[2]

@dbtest
def test_multiple_queries_with_special_command_same_line(executor, pgspecial):
    result = run(executor, "select 'foo'; \d", pgspecial=pgspecial)
    assert len(result) == 4  # 2 * (output+status)
    assert "foo" in result[0]
    # This is a lame check. :(
    assert "Schema" in result[2]

@dbtest
def test_multiple_queries_same_line_syntaxerror(executor, exception_formatter):
    result = run(executor, u"select 'fooé'; invalid syntax é",
                 exception_formatter=exception_formatter)
    assert u'fooé' in result[0]
    assert 'syntax error at or near "invalid"' in result[-1]


@pytest.fixture
def pgspecial():
    return PGSpecial()


@dbtest
def test_special_command_help(executor, pgspecial):
    result = run(executor, '\\?', pgspecial=pgspecial)[0].split('|')
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
    assert u'日本語' in run(executor, u"SELECT '日本語' AS japanese;", join=True)

@dbtest
def test_unicode_support_in_enum_type(executor):
    run(executor, u"CREATE TYPE mood AS ENUM ('sad', 'ok', 'happy', '日本語')")
    run(executor, u"CREATE TABLE person (name TEXT, current_mood mood)")
    run(executor, u"INSERT INTO person VALUES ('Moe', '日本語')")
    assert u'日本語' in run(executor, u"SELECT * FROM person", join=True)

@requires_json
def test_json_renders_without_u_prefix(executor, expanded):
    run(executor, u"create table jsontest(d json)")
    run(executor, u"""insert into jsontest (d) values ('{"name": "Éowyn"}')""")
    result = run(executor, u"SELECT d FROM jsontest LIMIT 1",
                 join=True, expanded=expanded)

    assert u'{"name": "Éowyn"}' in result


@requires_jsonb
def test_jsonb_renders_without_u_prefix(executor, expanded):
    run(executor, "create table jsonbtest(d jsonb)")
    run(executor, u"""insert into jsonbtest (d) values ('{"name": "Éowyn"}')""")
    result = run(executor, "SELECT d FROM jsonbtest LIMIT 1",
                 join=True, expanded=expanded)

    assert u'{"name": "Éowyn"}' in result

@dbtest
def test_date_time_types(executor):
    run(executor, "SET TIME ZONE UTC")
    assert run(executor, "SELECT (CAST('00:00:00' AS time))", join=True).split("\n")[3] \
         == "| 00:00:00 |"
    assert run(executor, "SELECT (CAST('00:00:00+14:59' AS timetz))", join=True).split("\n")[3]  \
        == "| 00:00:00+14:59 |"
    assert run(executor, "SELECT (CAST('4713-01-01 BC' AS date))", join=True).split("\n")[3] \
         == "| 4713-01-01 BC |"
    assert run(executor, "SELECT (CAST('4713-01-01 00:00:00 BC' AS timestamp))", join=True).split("\n")[3] \
         == "| 4713-01-01 00:00:00 BC |"
    assert run(executor, "SELECT (CAST('4713-01-01 00:00:00+00 BC' AS timestamptz))", join=True).split("\n")[3] \
         == "| 4713-01-01 00:00:00+00 BC |"
    assert run(executor, "SELECT (CAST('-123456789 days 12:23:56' AS interval))", join=True).split("\n")[3] \
         == "| -123456789 days, 12:23:56 |"

@dbtest
@pytest.mark.parametrize('value', ['10000000', '10000000.0', '10000000000000'])
def test_large_numbers_render_directly(executor, value):
    run(executor, "create table numbertest(a numeric)")
    run(executor,
        "insert into numbertest (a) values ({0})".format(value))
    value = format(float(value), ',g')
    assert value in run(executor, "select * from numbertest", join=True)


@dbtest
@pytest.mark.parametrize('command', ['di', 'dv', 'ds', 'df', 'dT'])
@pytest.mark.parametrize('verbose', ['', '+'])
@pytest.mark.parametrize('pattern', ['', 'x', '*.*', 'x.y', 'x.*', '*.y'])
def test_describe_special(executor, command, verbose, pattern):
    # We don't have any tests for the output of any of the special commands,
    # but we can at least make sure they run without error
    sql = r'\{command}{verbose} {pattern}'.format(**locals())
    executor.run(sql)


@dbtest
@pytest.mark.parametrize('sql', [
    'invalid sql',
    'SELECT 1; select error;',
])
def test_raises_with_no_formatter(executor, sql):
    with pytest.raises(psycopg2.ProgrammingError):
        list(executor.run(sql))


@dbtest
def test_on_error_resume(executor, exception_formatter):
    sql = 'select 1; error; select 1;'
    result = list(executor.run(sql, on_error_resume=True,
                               exception_formatter=exception_formatter))
    assert len(result) == 3


@dbtest
def test_on_error_stop(executor, exception_formatter):
    sql = 'select 1; error; select 1;'
    result = list(executor.run(sql, on_error_resume=False,
                               exception_formatter=exception_formatter))
    assert len(result) == 2

# @dbtest
# def test_unicode_notices(executor):
#     sql = "DO language plpgsql $$ BEGIN RAISE NOTICE '有人更改'; END $$;"
#     result = list(executor.run(sql))
#     assert result[0][0] == u'NOTICE:  有人更改\n'
