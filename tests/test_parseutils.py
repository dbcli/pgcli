import pytest
from pgcli.packages.parseutils import extract_tables
from pgcli.packages.parseutils import find_prev_keyword

def test_empty_string():
    tables = extract_tables('')
    assert tables == []

def test_simple_select_single_table():
    tables = extract_tables('select * from abc')
    assert tables == [(None, 'abc', None)]

def test_simple_select_single_table_schema_qualified():
    tables = extract_tables('select * from abc.def')
    assert tables == [('abc', 'def', None)]

def test_simple_select_single_table_double_quoted():
    tables = extract_tables('select * from "Abc"')
    assert tables == [(None, 'Abc', None)]

def test_simple_select_multiple_tables():
    tables = extract_tables('select * from abc, def')
    assert sorted(tables) == [(None, 'abc', None), (None, 'def', None)]

def test_simple_select_multiple_tables_double_quoted():
    tables = extract_tables('select * from "Abc", "Def"')
    assert tables == [(None, 'Abc', None), (None, 'Def', None)]

def test_simple_select_single_table_deouble_quoted_aliased():
    tables = extract_tables('select * from "Abc" a')
    assert tables == [(None, 'Abc', 'a')]

def test_simple_select_multiple_tables_deouble_quoted_aliased():
    tables = extract_tables('select * from "Abc" a, "Def" d')
    assert tables == [(None, 'Abc', 'a'), (None, 'Def', 'd')]

def test_simple_select_multiple_tables_schema_qualified():
    tables = extract_tables('select * from abc.def, ghi.jkl')
    assert sorted(tables) == [('abc', 'def', None), ('ghi', 'jkl', None)]

def test_simple_select_with_cols_single_table():
    tables = extract_tables('select a,b from abc')
    assert tables == [(None, 'abc', None)]

def test_simple_select_with_cols_single_table_schema_qualified():
    tables = extract_tables('select a,b from abc.def')
    assert tables == [('abc', 'def', None)]

def test_simple_select_with_cols_multiple_tables():
    tables = extract_tables('select a,b from abc, def')
    assert sorted(tables) == [(None, 'abc', None), (None, 'def', None)]

def test_simple_select_with_cols_multiple_tables():
    tables = extract_tables('select a,b from abc.def, def.ghi')
    assert sorted(tables) == [('abc', 'def', None), ('def', 'ghi', None)]

def test_select_with_hanging_comma_single_table():
    tables = extract_tables('select a, from abc')
    assert tables == [(None, 'abc', None)]

def test_select_with_hanging_comma_multiple_tables():
    tables = extract_tables('select a, from abc, def')
    assert sorted(tables) == [(None, 'abc', None), (None, 'def', None)]

def test_select_with_hanging_period_multiple_tables():
    tables = extract_tables('SELECT t1. FROM tabl1 t1, tabl2 t2')
    assert sorted(tables) == [(None, 'tabl1', 't1'), (None, 'tabl2', 't2')]

def test_simple_insert_single_table():
    tables = extract_tables('insert into abc (id, name) values (1, "def")')

    # sqlparse mistakenly assigns an alias to the table
    # assert tables == [(None, 'abc', None)]
    assert tables == [(None, 'abc', 'abc')]

@pytest.mark.xfail
def test_simple_insert_single_table_schema_qualified():
    tables = extract_tables('insert into abc.def (id, name) values (1, "def")')
    assert tables == [('abc', 'def', None)]

def test_simple_update_table():
    tables = extract_tables('update abc set id = 1')
    assert tables == [(None, 'abc', None)]

def test_simple_update_table():
    tables = extract_tables('update abc.def set id = 1')
    assert tables == [('abc', 'def', None)]

@pytest.mark.parametrize('join_type', ['', 'INNER', 'LEFT', 'RIGHT OUTER'])
def test_join_table(join_type):
    sql = 'SELECT * FROM abc a {0} JOIN def d ON a.id = d.num'.format(join_type)
    tables = extract_tables(sql)
    assert sorted(tables) == [(None, 'abc', 'a'), (None, 'def', 'd')]

def test_join_table_schema_qualified():
    tables = extract_tables('SELECT * FROM abc.def x JOIN ghi.jkl y ON x.id = y.num')
    assert tables == [('abc', 'def', 'x'), ('ghi', 'jkl', 'y')]

def test_join_as_table():
    tables = extract_tables('SELECT * FROM my_table AS m WHERE m.a > 5')
    assert tables == [(None, 'my_table', 'm')]

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
