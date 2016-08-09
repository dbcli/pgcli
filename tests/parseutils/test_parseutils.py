import pytest
from pgcli.packages.parseutils.tables import extract_tables
from pgcli.packages.parseutils.utils import find_prev_keyword, is_open_quote

def test_empty_string():
    tables = extract_tables('')
    assert tables == ()

def test_simple_select_single_table():
    tables = extract_tables('select * from abc')
    assert tables == ((None, 'abc', None, False),)


@pytest.mark.parametrize('sql', [
    'select * from "abc"."def"',
    'select * from abc."def"',
])
def test_simple_select_single_table_schema_qualified_quoted_table(sql):
    tables = extract_tables(sql)
    assert tables == (('abc', 'def', '"def"', False),)


@pytest.mark.parametrize('sql', [
    'select * from abc.def',
    'select * from "abc".def',
])
def test_simple_select_single_table_schema_qualified(sql):
    tables = extract_tables(sql)
    assert tables == (('abc', 'def', None, False),)


def test_simple_select_single_table_double_quoted():
    tables = extract_tables('select * from "Abc"')
    assert tables == ((None, 'Abc', None, False),)

def test_simple_select_multiple_tables():
    tables = extract_tables('select * from abc, def')
    assert set(tables) == set([(None, 'abc', None, False),
                               (None, 'def', None, False)])

def test_simple_select_multiple_tables_double_quoted():
    tables = extract_tables('select * from "Abc", "Def"')
    assert set(tables) == set([(None, 'Abc', None, False),
                               (None, 'Def', None, False)])

def test_simple_select_single_table_deouble_quoted_aliased():
    tables = extract_tables('select * from "Abc" a')
    assert tables == ((None, 'Abc', 'a', False),)

def test_simple_select_multiple_tables_deouble_quoted_aliased():
    tables = extract_tables('select * from "Abc" a, "Def" d')
    assert set(tables) == set([(None, 'Abc', 'a', False),
                               (None, 'Def', 'd', False)])

def test_simple_select_multiple_tables_schema_qualified():
    tables = extract_tables('select * from abc.def, ghi.jkl')
    assert set(tables) == set([('abc', 'def', None, False),
                               ('ghi', 'jkl', None, False)])

def test_simple_select_with_cols_single_table():
    tables = extract_tables('select a,b from abc')
    assert tables == ((None, 'abc', None, False),)

def test_simple_select_with_cols_single_table_schema_qualified():
    tables = extract_tables('select a,b from abc.def')
    assert tables == (('abc', 'def', None, False),)

def test_simple_select_with_cols_multiple_tables():
    tables = extract_tables('select a,b from abc, def')
    assert set(tables) == set([(None, 'abc', None, False),
                               (None, 'def', None, False)])

def test_simple_select_with_cols_multiple_qualified_tables():
    tables = extract_tables('select a,b from abc.def, def.ghi')
    assert set(tables) == set([('abc', 'def', None, False),
                               ('def', 'ghi', None, False)])

def test_select_with_hanging_comma_single_table():
    tables = extract_tables('select a, from abc')
    assert tables == ((None, 'abc', None, False),)

def test_select_with_hanging_comma_multiple_tables():
    tables = extract_tables('select a, from abc, def')
    assert set(tables) == set([(None, 'abc', None, False),
                               (None, 'def', None, False)])

def test_select_with_hanging_period_multiple_tables():
    tables = extract_tables('SELECT t1. FROM tabl1 t1, tabl2 t2')
    assert set(tables) == set([(None, 'tabl1', 't1', False),
                               (None, 'tabl2', 't2', False)])

def test_simple_insert_single_table():
    tables = extract_tables('insert into abc (id, name) values (1, "def")')

    # sqlparse mistakenly assigns an alias to the table
    # AND mistakenly identifies the field list as
    # assert tables == ((None, 'abc', 'abc', False),)

    assert tables == ((None, 'abc', 'abc', False),)

@pytest.mark.xfail
def test_simple_insert_single_table_schema_qualified():
    tables = extract_tables('insert into abc.def (id, name) values (1, "def")')
    assert tables == (('abc', 'def', None, False),)

def test_simple_update_table_no_schema():
    tables = extract_tables('update abc set id = 1')
    assert tables == ((None, 'abc', None, False),)

def test_simple_update_table_with_schema():
    tables = extract_tables('update abc.def set id = 1')
    assert tables == (('abc', 'def', None, False),)

@pytest.mark.parametrize('join_type', ['', 'INNER', 'LEFT', 'RIGHT OUTER'])
def test_join_table(join_type):
    sql = 'SELECT * FROM abc a {0} JOIN def d ON a.id = d.num'.format(join_type)
    tables = extract_tables(sql)
    assert set(tables) == set([(None, 'abc', 'a', False),
                               (None, 'def', 'd', False)])

def test_join_table_schema_qualified():
    tables = extract_tables('SELECT * FROM abc.def x JOIN ghi.jkl y ON x.id = y.num')
    assert set(tables) == set([('abc', 'def', 'x', False),
                               ('ghi', 'jkl', 'y', False)])


def test_incomplete_join_clause():
    sql = '''select a.x, b.y
             from abc a join bcd b
             on a.id = '''
    tables = extract_tables(sql)
    assert tables == ((None, 'abc', 'a', False),
                      (None, 'bcd', 'b', False))


def test_join_as_table():
    tables = extract_tables('SELECT * FROM my_table AS m WHERE m.a > 5')
    assert tables == ((None, 'my_table', 'm', False),)


def test_multiple_joins():
    sql = '''select * from t1
            inner join t2 ON
              t1.id = t2.t1_id
            inner join t3 ON
              t2.id = t3.'''
    tables = extract_tables(sql)
    assert tables == (
        (None, 't1', None, False),
        (None, 't2', None, False),
        (None, 't3', None, False))


def test_subselect_tables():
    sql = 'SELECT * FROM (SELECT  FROM abc'
    tables = extract_tables(sql)
    assert tables == ((None, 'abc', None, False),)

@pytest.mark.parametrize('text', ['SELECT * FROM foo.', 'SELECT 123 AS foo'])
def test_extract_no_tables(text):
    tables = extract_tables(text)
    assert tables == tuple()

@pytest.mark.parametrize('arg_list', ['', 'arg1', 'arg1, arg2, arg3'])
def test_simple_function_as_table(arg_list):
    tables = extract_tables('SELECT * FROM foo({0})'.format(arg_list))
    assert tables == ((None, 'foo', None, True),)

@pytest.mark.parametrize('arg_list', ['', 'arg1', 'arg1, arg2, arg3'])
def test_simple_schema_qualified_function_as_table(arg_list):
    tables = extract_tables('SELECT * FROM foo.bar({0})'.format(arg_list))
    assert tables == (('foo', 'bar', None, True),)

@pytest.mark.parametrize('arg_list', ['', 'arg1', 'arg1, arg2, arg3'])
def test_simple_aliased_function_as_table(arg_list):
    tables = extract_tables('SELECT * FROM foo({0}) bar'.format(arg_list))
    assert tables == ((None, 'foo', 'bar', True),)


def test_simple_table_and_function():
    tables = extract_tables('SELECT * FROM foo JOIN bar()')
    assert set(tables) == set([(None, 'foo', None, False),
                               (None, 'bar', None, True)])

def test_complex_table_and_function():
    tables = extract_tables('''SELECT * FROM foo.bar baz
                               JOIN bar.qux(x, y, z) quux''')
    assert set(tables) == set([('foo', 'bar', 'baz', False),
                               ('bar', 'qux', 'quux', True)])



def test_find_prev_keyword_using():
    q = 'select * from tbl1 inner join tbl2 using (col1, '
    kw, q2 = find_prev_keyword(q)
    assert kw.value == '(' and q2 == 'select * from tbl1 inner join tbl2 using ('

@pytest.mark.parametrize('sql', [
    'select * from foo where bar',
    'select * from foo where bar = 1 and baz or ',
    'select * from foo where bar = 1 and baz between qux and ',
])
def test_find_prev_keyword_where(sql):
    kw, stripped = find_prev_keyword(sql)
    assert kw.value == 'where' and stripped == 'select * from foo where'


@pytest.mark.parametrize('sql', [
    'create table foo (bar int, baz ',
    'select * from foo() as bar (baz '
])
def test_find_prev_keyword_open_parens(sql):
    kw, _ = find_prev_keyword(sql)
    assert kw.value == '('


@pytest.mark.parametrize('sql', [
    '',
    '$$ foo $$',
    "$$ 'foo' $$",
    '$$ "foo" $$',
    '$$ $a$ $$',
    '$a$ $$ $a$',
    'foo bar $$ baz $$',
])
def test_is_open_quote__closed(sql):
    assert not is_open_quote(sql)


@pytest.mark.parametrize('sql', [
    '$$',
    ';;;$$',
    'foo $$ bar $$; foo $$',
    '$$ foo $a$',
    "foo 'bar baz",
    "$a$ foo ",
    '$$ "foo" ',
    '$$ $a$ ',
    'foo bar $$ baz',
])
def test_is_open_quote__open(sql):
    assert is_open_quote(sql)
