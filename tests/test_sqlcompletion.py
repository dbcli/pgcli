from pgcli.packages.sqlcompletion import (
    suggest_type, Special, Database, Schema, Table, Column, View, Keyword,
    Function, Datatype, Alias)
import pytest


def test_select_suggests_cols_with_visible_table_scope():
    suggestions = suggest_type('SELECT  FROM tabl', 'SELECT ')
    assert set(suggestions) == set([
        Column(tables=((None, 'tabl', None, False),)),
        Function(schema=None),
        Keyword()
    ])


def test_select_suggests_cols_with_qualified_table_scope():
    suggestions = suggest_type('SELECT  FROM sch.tabl', 'SELECT ')
    assert set(suggestions) == set([
        Column(tables=(('sch', 'tabl', None, False),)),
        Function(schema=None),
        Keyword()
    ])


@pytest.mark.parametrize('expression', [
    'SELECT * FROM tabl WHERE ',
    'SELECT * FROM "tabl" WHERE ',
    'SELECT * FROM tabl WHERE (',
    'SELECT * FROM tabl WHERE foo = ',
    'SELECT * FROM tabl WHERE bar OR ',
    'SELECT * FROM tabl WHERE foo = 1 AND ',
    'SELECT * FROM tabl WHERE (bar > 10 AND ',
    'SELECT * FROM tabl WHERE (bar AND (baz OR (qux AND (',
    'SELECT * FROM tabl WHERE 10 < ',
    'SELECT * FROM tabl WHERE foo BETWEEN ',
    'SELECT * FROM tabl WHERE foo BETWEEN foo AND ',
])
def test_where_suggests_columns_functions(expression):
    suggestions = suggest_type(expression, expression)
    assert set(suggestions) == set([
        Column(tables=((None, 'tabl', None, False),)),
        Function(schema=None),
        Keyword(),
    ])


@pytest.mark.parametrize('expression', [
    'SELECT * FROM tabl WHERE foo IN (',
    'SELECT * FROM tabl WHERE foo IN (bar, ',
])
def test_where_in_suggests_columns(expression):
    suggestions = suggest_type(expression, expression)
    assert set(suggestions) == set([
        Column(tables=((None, 'tabl', None, False),)),
        Function(schema=None),
        Keyword(),
    ])


def test_where_equals_any_suggests_columns_or_keywords():
    text = 'SELECT * FROM tabl WHERE foo = ANY('
    suggestions = suggest_type(text, text)
    assert set(suggestions) == set([
        Column(tables=((None, 'tabl', None, False),)),
        Function(schema=None),
        Keyword(),
    ])


def test_lparen_suggests_cols():
    suggestion = suggest_type('SELECT MAX( FROM tbl', 'SELECT MAX(')
    assert set(suggestion) == set([
        Column(tables=((None, 'tbl', None, False),))])


def test_select_suggests_cols_and_funcs():
    suggestions = suggest_type('SELECT ', 'SELECT ')
    assert set(suggestions) == set([
         Column(tables=()),
         Function(schema=None),
         Keyword(),
    ])


@pytest.mark.parametrize('expression', [
    'INSERT INTO ',
    'COPY ',
    'UPDATE ',
    'DESCRIBE ',
])
def test_suggests_tables_views_and_schemas(expression):
    suggestions = suggest_type(expression, expression)
    assert set(suggestions) == set([
        Table(schema=None),
        View(schema=None),
        Schema(),
    ])


@pytest.mark.parametrize('expression', [
    'SELECT * FROM ',
    'SELECT * FROM foo JOIN ',
])
def test_suggest_tables_views_schemas_and_set_returning_functions(expression):
    suggestions = suggest_type(expression, expression)
    assert set(suggestions) == set([
        Table(schema=None),
        View(schema=None),
        Function(schema=None, filter='is_set_returning'),
        Schema(),
    ])


@pytest.mark.parametrize('expression', [
    'INSERT INTO sch.',
    'COPY sch.',
    'UPDATE sch.',
    'DESCRIBE sch.',
])
def test_suggest_qualified_tables_and_views(expression):
    suggestions = suggest_type(expression, expression)
    assert set(suggestions) == set([
        Table(schema='sch'),
        View(schema='sch'),
    ])


@pytest.mark.parametrize('expression', [
    'SELECT * FROM sch.',
    'SELECT * FROM sch."',
    'SELECT * FROM sch."foo',
    'SELECT * FROM "sch".',
    'SELECT * FROM "sch"."',
    'SELECT * FROM foo JOIN sch.',
])
def test_suggest_qualified_tables_views_and_set_returning_functions(expression):
    suggestions = suggest_type(expression, expression)
    assert set(suggestions) == set([
        Table(schema='sch'),
        View(schema='sch'),
        Function(schema='sch', filter='is_set_returning'),
    ])


def test_truncate_suggests_tables_and_schemas():
    suggestions = suggest_type('TRUNCATE ', 'TRUNCATE ')
    assert set(suggestions) == set([
        Table(schema=None),
        Schema()])


def test_truncate_suggests_qualified_tables():
    suggestions = suggest_type('TRUNCATE sch.', 'TRUNCATE sch.')
    assert set(suggestions) == set([
        Table(schema='sch')])


def test_distinct_suggests_cols():
    suggestions = suggest_type('SELECT DISTINCT ', 'SELECT DISTINCT ')
    assert suggestions ==(Column(tables=()),)


def test_col_comma_suggests_cols():
    suggestions = suggest_type('SELECT a, b, FROM tbl', 'SELECT a, b,')
    assert set(suggestions) == set([
        Column(tables=((None, 'tbl', None, False),)),
        Function(schema=None),
        Keyword(),
    ])


def test_table_comma_suggests_tables_and_schemas():
    suggestions = suggest_type('SELECT a, b FROM tbl1, ',
            'SELECT a, b FROM tbl1, ')
    assert set(suggestions) == set([
        Table(schema=None),
        View(schema=None),
        Function(schema=None, filter='is_set_returning'),
        Schema(),
    ])


def test_into_suggests_tables_and_schemas():
    suggestion = suggest_type('INSERT INTO ', 'INSERT INTO ')
    assert set(suggestion) == set([
        Table(schema=None),
        View(schema=None),
        Schema(),
    ])


def test_insert_into_lparen_suggests_cols():
    suggestions = suggest_type('INSERT INTO abc (', 'INSERT INTO abc (')
    assert suggestions ==(Column(tables=((None, 'abc', None, False),)),)


def test_insert_into_lparen_partial_text_suggests_cols():
    suggestions = suggest_type('INSERT INTO abc (i', 'INSERT INTO abc (i')
    assert suggestions ==(Column(tables=((None, 'abc', None, False),)),)


def test_insert_into_lparen_comma_suggests_cols():
    suggestions = suggest_type('INSERT INTO abc (id,', 'INSERT INTO abc (id,')
    assert suggestions ==(Column(tables=((None, 'abc', None, False),)),)


def test_partially_typed_col_name_suggests_col_names():
    suggestions = suggest_type('SELECT * FROM tabl WHERE col_n',
            'SELECT * FROM tabl WHERE col_n')
    assert set(suggestions) == set([
        Column(tables=((None, 'tabl', None, False),)),
        Function(schema=None),
        Keyword()
    ])


def test_dot_suggests_cols_of_a_table_or_schema_qualified_table():
    suggestions = suggest_type('SELECT tabl. FROM tabl', 'SELECT tabl.')
    assert set(suggestions) == set([
        Column(tables=((None, 'tabl', None, False),)),
        Table(schema='tabl'),
        View(schema='tabl'),
        Function(schema='tabl'),
    ])


@pytest.mark.parametrize('sql', [
    'SELECT t1. FROM tabl1 t1',
    'SELECT t1. FROM tabl1 t1, tabl2 t2',
    'SELECT t1. FROM "tabl1" t1',
    'SELECT t1. FROM "tabl1" t1, "tabl2" t2',
    ])
def test_dot_suggests_cols_of_an_alias(sql):
    suggestions = suggest_type(sql, 'SELECT t1.')
    assert set(suggestions) == set([
        Table(schema='t1'),
        View(schema='t1'),
        Column(tables=((None, 'tabl1', 't1', False),)),
        Function(schema='t1'),
    ])


@pytest.mark.parametrize('sql', [
    'SELECT * FROM tabl1 t1 WHERE t1.',
    'SELECT * FROM tabl1 t1, tabl2 t2 WHERE t1.',
    'SELECT * FROM "tabl1" t1 WHERE t1.',
    'SELECT * FROM "tabl1" t1, tabl2 t2 WHERE t1.',
    ])
def test_dot_suggests_cols_of_an_alias_where(sql):
    suggestions = suggest_type(sql, sql)
    assert set(suggestions) == set([
        Table(schema='t1'),
        View(schema='t1'),
        Column(tables=((None, 'tabl1', 't1', False),)),
        Function(schema='t1'),
    ])


def test_dot_col_comma_suggests_cols_or_schema_qualified_table():
    suggestions = suggest_type('SELECT t1.a, t2. FROM tabl1 t1, tabl2 t2',
            'SELECT t1.a, t2.')
    assert set(suggestions) == set([
        Column(tables=((None, 'tabl2', 't2', False),)),
        Table(schema='t2'),
        View(schema='t2'),
        Function(schema='t2'),
    ])


@pytest.mark.parametrize('expression', [
    'SELECT * FROM (',
    'SELECT * FROM foo WHERE EXISTS (',
    'SELECT * FROM foo WHERE bar AND NOT EXISTS (',
])
def test_sub_select_suggests_keyword(expression):
    suggestion = suggest_type(expression, expression)
    assert suggestion == (Keyword(),)


@pytest.mark.parametrize('expression', [
    'SELECT * FROM (S',
    'SELECT * FROM foo WHERE EXISTS (S',
    'SELECT * FROM foo WHERE bar AND NOT EXISTS (S',
])
def test_sub_select_partial_text_suggests_keyword(expression):
    suggestion = suggest_type(expression, expression)
    assert suggestion ==(Keyword(),)


def test_outer_table_reference_in_exists_subquery_suggests_columns():
    q = 'SELECT * FROM foo f WHERE EXISTS (SELECT 1 FROM bar WHERE f.'
    suggestions = suggest_type(q, q)
    assert set(suggestions) == set([
        Column(tables=((None, 'foo', 'f', False),)),
        Table(schema='f'),
        View(schema='f'),
        Function(schema='f'),
    ])


@pytest.mark.parametrize('expression', [
    'SELECT * FROM (SELECT * FROM ',
    'SELECT * FROM foo WHERE EXISTS (SELECT * FROM ',
    'SELECT * FROM foo WHERE bar AND NOT EXISTS (SELECT * FROM ',
])
def test_sub_select_table_name_completion(expression):
    suggestion = suggest_type(expression, expression)
    assert set(suggestion) == set([
        Table(schema=None),
        View(schema=None),
        Function(schema=None, filter='is_set_returning'),
        Schema(),
    ])


def test_sub_select_col_name_completion():
    suggestions = suggest_type('SELECT * FROM (SELECT  FROM abc',
            'SELECT * FROM (SELECT ')
    assert set(suggestions) == set([
        Column(tables=((None, 'abc', None, False),)),
        Function(schema=None),
        Keyword(),
    ])


@pytest.mark.xfail
def test_sub_select_multiple_col_name_completion():
    suggestions = suggest_type('SELECT * FROM (SELECT a, FROM abc',
            'SELECT * FROM (SELECT a, ')
    assert set(suggestions) == set([
        Column(tables=((None, 'abc', None, False),)),
        Function(schema=None),
        Keyword(),
    ])


def test_sub_select_dot_col_name_completion():
    suggestions = suggest_type('SELECT * FROM (SELECT t. FROM tabl t',
            'SELECT * FROM (SELECT t.')
    assert set(suggestions) == set([
        Column(tables=((None, 'tabl', 't', False),)),
        Table(schema='t'),
        View(schema='t'),
        Function(schema='t'),
    ])


@pytest.mark.parametrize('join_type',('', 'INNER', 'LEFT', 'RIGHT OUTER',))
@pytest.mark.parametrize('tbl_alias',('', 'foo',))
def test_join_suggests_tables_and_schemas(tbl_alias, join_type):
    text = 'SELECT * FROM abc {0} {1} JOIN '.format(tbl_alias, join_type)
    suggestion = suggest_type(text, text)
    assert set(suggestion) == set([
        Table(schema=None),
        View(schema=None),
        Function(schema=None, filter='is_set_returning'),
        Schema(),
    ])


def test_left_join_with_comma():
    text = 'select * from foo f left join bar b,'
    suggestions = suggest_type(text, text)
    assert set(suggestions) == set([
         Table(schema=None),
         View(schema=None),
         Function(schema=None, filter='is_set_returning'),
         Schema(),
    ])


@pytest.mark.parametrize('sql', [
    'SELECT * FROM abc a JOIN def d ON a.',
    'SELECT * FROM abc a JOIN def d ON a.id = d.id AND a.',
])
def test_join_alias_dot_suggests_cols1(sql):
    suggestions = suggest_type(sql, sql)
    assert set(suggestions) == set([
        Column(tables=((None, 'abc', 'a', False),)),
        Table(schema='a'),
        View(schema='a'),
        Function(schema='a'),
    ])


@pytest.mark.parametrize('sql', [
    'SELECT * FROM abc a JOIN def d ON a.id = d.',
    'SELECT * FROM abc a JOIN def d ON a.id = d.id AND a.id2 = d.',
])
def test_join_alias_dot_suggests_cols2(sql):
    suggestion = suggest_type(sql, sql)
    assert set(suggestion) == set([
        Column(tables=((None, 'def', 'd', False),)),
        Table(schema='d'),
        View(schema='d'),
        Function(schema='d'),
    ])


@pytest.mark.parametrize('sql', [
    'select a.x, b.y from abc a join bcd b on ',
    'select a.x, b.y from abc a join bcd b on a.id = b.id OR ',
])
def test_on_suggests_aliases(sql):
    suggestions = suggest_type(sql, sql)
    assert suggestions == (Alias(aliases=('a', 'b',)),)


@pytest.mark.parametrize('sql', [
    'select abc.x, bcd.y from abc join bcd on ',
    'select abc.x, bcd.y from abc join bcd on abc.id = bcd.id AND ',
])
def test_on_suggests_tables(sql):
    suggestions = suggest_type(sql, sql)
    assert suggestions == (Alias(aliases=('abc', 'bcd',)),)


@pytest.mark.parametrize('sql', [
    'select a.x, b.y from abc a join bcd b on a.id = ',
    'select a.x, b.y from abc a join bcd b on a.id = b.id AND a.id2 = ',
])
def test_on_suggests_aliases_right_side(sql):
    suggestions = suggest_type(sql, sql)
    assert suggestions == (Alias(aliases=('a', 'b',)),)


@pytest.mark.parametrize('sql', [
    'select abc.x, bcd.y from abc join bcd on ',
    'select abc.x, bcd.y from abc join bcd on abc.id = bcd.id and ',
])
def test_on_suggests_tables_right_side(sql):
    suggestions = suggest_type(sql, sql)
    assert suggestions == (Alias(aliases=('abc', 'bcd',)),)


@pytest.mark.parametrize('col_list', ('', 'col1, ',))
def test_join_using_suggests_common_columns(col_list):
    text = 'select * from abc inner join def using (' + col_list
    assert set(suggest_type(text, text)) == set([
        Column(tables=((None, 'abc', None, False),
                       (None, 'def', None, False)),
               drop_unique=True),
    ])


def test_2_statements_2nd_current():
    suggestions = suggest_type('select * from a; select * from ',
                               'select * from a; select * from ')
    assert set(suggestions) == set([
        Table(schema=None),
        View(schema=None),
        Function(schema=None, filter='is_set_returning'),
        Schema(),
    ])

    suggestions = suggest_type('select * from a; select  from b',
                               'select * from a; select ')
    assert set(suggestions) == set([
        Column(tables=((None, 'b', None, False),)),
        Function(schema=None),
        Keyword()
    ])

    # Should work even if first statement is invalid
    suggestions = suggest_type('select * from; select * from ',
                               'select * from; select * from ')
    assert set(suggestions) == set([
        Table(schema=None),
        View(schema=None),
        Function(schema=None, filter='is_set_returning'),
        Schema(),
    ])


def test_2_statements_1st_current():
    suggestions = suggest_type('select * from ; select * from b',
                               'select * from ')
    assert set(suggestions) == set([
        Table(schema=None),
        View(schema=None),
        Function(schema=None, filter='is_set_returning'),
        Schema(),
    ])

    suggestions = suggest_type('select  from a; select * from b',
                               'select ')
    assert set(suggestions) == set([
        Column(tables=((None, 'a', None, False),)),
        Function(schema=None),
        Keyword()
    ])


def test_3_statements_2nd_current():
    suggestions = suggest_type('select * from a; select * from ; select * from c',
                               'select * from a; select * from ')
    assert set(suggestions) == set([
        Table(schema=None),
        View(schema=None),
        Function(schema=None, filter='is_set_returning'),
        Schema(),
    ])

    suggestions = suggest_type('select * from a; select  from b; select * from c',
                               'select * from a; select ')
    assert set(suggestions) == set([
        Column(tables=((None, 'b', None, False),)),
        Function(schema=None),
        Keyword()
    ])


def test_create_db_with_template():
    suggestions = suggest_type('create database foo with template ',
                               'create database foo with template ')

    assert set(suggestions) == set((Database(),))


@pytest.mark.parametrize('initial_text',('', '    ', '\t \t',))
def test_specials_included_for_initial_completion(initial_text):
    suggestions = suggest_type(initial_text, initial_text)

    assert set(suggestions) == \
        set([Keyword(), Special()])


def test_drop_schema_qualified_table_suggests_only_tables():
    text = 'DROP TABLE schema_name.table_name'
    suggestions = suggest_type(text, text)
    assert suggestions ==(Table(schema='schema_name'),)


@pytest.mark.parametrize('text',(',', '  ,', 'sel ,',))
def test_handle_pre_completion_comma_gracefully(text):
    suggestions = suggest_type(text, text)

    assert iter(suggestions)


def test_drop_schema_suggests_schemas():
    sql = 'DROP SCHEMA '
    assert suggest_type(sql, sql) ==(Schema(),)


@pytest.mark.parametrize('text', [
    'SELECT x::',
    'SELECT x::y',
    'SELECT (x + y)::',
])
def test_cast_operator_suggests_types(text):
    assert set(suggest_type(text, text)) == set([
        Datatype(schema=None),
        Table(schema=None),
        Schema()])


@pytest.mark.parametrize('text', [
    'SELECT foo::bar.',
    'SELECT foo::bar.baz',
    'SELECT (x + y)::bar.',
])
def test_cast_operator_suggests_schema_qualified_types(text):
    assert set(suggest_type(text, text)) == set([
        Datatype(schema='bar'),
        Table(schema='bar')])


def test_alter_column_type_suggests_types():
    q = 'ALTER TABLE foo ALTER COLUMN bar TYPE '
    assert set(suggest_type(q, q)) == set([
        Datatype(schema=None),
        Table(schema=None),
        Schema()])


@pytest.mark.parametrize('text', [
    'CREATE TABLE foo (bar ',
    'CREATE TABLE foo (bar DOU',
    'CREATE TABLE foo (bar INT, baz ',
    'CREATE TABLE foo (bar INT, baz TEXT, qux ',
    'CREATE FUNCTION foo (bar ',
    'CREATE FUNCTION foo (bar INT, baz ',
    'SELECT * FROM foo() AS bar (baz ',
    'SELECT * FROM foo() AS bar (baz INT, qux ',

    # make sure this doesnt trigger special completion
    'CREATE TABLE foo (dt d',
])
def test_identifier_suggests_types_in_parentheses(text):
    assert set(suggest_type(text, text)) == set([
        Datatype(schema=None),
        Table(schema=None),
        Schema()])


@pytest.mark.parametrize('text', [
    'SELECT foo ',
    'SELECT foo FROM bar ',
    'SELECT foo AS bar ',
    'SELECT foo bar ',
    'SELECT * FROM foo AS bar ',
    'SELECT * FROM foo bar ',
    'SELECT foo FROM (SELECT bar '
])
def test_alias_suggests_keywords(text):
    suggestions = suggest_type(text, text)
    assert suggestions ==(Keyword(),)


def test_invalid_sql():
    # issue 317
    text = 'selt *'
    suggestions = suggest_type(text, text)
    assert suggestions ==(Keyword(),)


@pytest.mark.parametrize('text', [
    'SELECT * FROM foo where created > now() - ',
    'select * from foo where bar ',
])
def test_suggest_where_keyword(text):
    # https://github.com/dbcli/mycli/issues/135
    suggestions = suggest_type(text, text)
    assert set(suggestions) == set([
        Column(tables=((None, 'foo', None, False),)),
        Function(schema=None),
        Keyword(),
    ])


@pytest.mark.parametrize('text, before, expected', [
    ('\\ns abc SELECT ', 'SELECT ', [
        Column(tables=()),
        Function(schema=None),
        Keyword()
    ]),
    ('\\ns abc SELECT foo ', 'SELECT foo ',(Keyword(),)),
    ('\\ns abc SELECT t1. FROM tabl1 t1', 'SELECT t1.', [
        Table(schema='t1'),
        View(schema='t1'),
        Column(tables=((None, 'tabl1', 't1', False),)),
        Function(schema='t1')
    ])
])
def test_named_query_completion(text, before, expected):
    suggestions = suggest_type(text, before)
    assert set(expected) == set(suggestions)


def test_select_suggests_fields_from_function():
    suggestions = suggest_type('SELECT  FROM func()', 'SELECT ')
    assert set(suggestions) == set([
            Column(tables=((None, 'func', None, True),)),
            Function(schema=None),
            Keyword()
            ])


@pytest.mark.parametrize('sql', [
    'select * from "',
    'select * from "foo',
])
def test_ignore_leading_double_quotes(sql):
    suggestions = suggest_type(sql, sql)
    assert Table(schema=None) in set(suggestions)

