from pgcli.packages.sqlcompletion import suggest_type
import pytest

def test_select_suggests_cols_with_table_scope():
    suggestion = suggest_type('SELECT  FROM tabl', 'SELECT ')
    assert suggestion == ('columns-and-functions', ['tabl'])

def test_where_suggests_columns_functions():
    suggestion = suggest_type('SELECT * FROM tabl WHERE ',
            'SELECT * FROM tabl WHERE ')
    assert suggestion == ('columns-and-functions', ['tabl'])

def test_lparen_suggests_cols():
    suggestion = suggest_type('SELECT MAX( FROM tbl', 'SELECT MAX(')
    assert suggestion == ('columns', ['tbl'])

def test_select_suggests_cols_and_funcs():
    suggestion = suggest_type('SELECT ', 'SELECT ')
    assert suggestion == ('columns-and-functions', [])

def test_from_suggests_tables():
    suggestion = suggest_type('SELECT * FROM ', 'SELECT * FROM ')
    assert suggestion == ('tables', [])

def test_distinct_suggests_cols():
    suggestion = suggest_type('SELECT DISTINCT ', 'SELECT DISTINCT ')
    assert suggestion == ('columns', [])

def test_col_comma_suggests_cols():
    suggestion = suggest_type('SELECT a, b, FROM tbl', 'SELECT a, b,')
    assert suggestion == ('columns-and-functions', ['tbl'])

def test_table_comma_suggests_tables():
    suggestion = suggest_type('SELECT a, b FROM tbl1, ',
            'SELECT a, b FROM tbl1, ')
    assert suggestion == ('tables', [])

def test_into_suggests_tables():
    suggestion = suggest_type('INSERT INTO ', 'INSERT INTO ')
    assert suggestion == ('tables', [])

def test_insert_into_lparen_suggests_cols():
    suggestion = suggest_type('INSERT INTO abc (', 'INSERT INTO abc (')
    assert suggestion == ('columns', ['abc'])

def test_insert_into_lparen_partial_text_suggests_cols():
    suggestion = suggest_type('INSERT INTO abc (i', 'INSERT INTO abc (i')
    assert suggestion == ('columns', ['abc'])

def test_insert_into_lparen_comma_suggests_cols():
    suggestion = suggest_type('INSERT INTO abc (id,', 'INSERT INTO abc (id,')
    assert suggestion == ('columns', ['abc'])

def test_partially_typed_col_name_suggests_col_names():
    suggestion = suggest_type('SELECT * FROM tabl WHERE col_n',
            'SELECT * FROM tabl WHERE col_n')
    assert suggestion == ('columns-and-functions', ['tabl'])

def test_dot_suggests_cols_of_a_table():
    suggestion = suggest_type('SELECT tabl. FROM tabl', 'SELECT tabl.')
    assert suggestion == ('columns', ['tabl'])

def test_dot_suggests_cols_of_an_alias():
    suggestion = suggest_type('SELECT t1. FROM tabl1 t1, tabl2 t2',
            'SELECT t1.')
    assert suggestion == ('columns', ['tabl1'])

def test_dot_col_comma_suggests_cols():
    suggestion = suggest_type('SELECT t1.a, t2. FROM tabl1 t1, tabl2 t2',
            'SELECT t1.a, t2.')
    assert suggestion == ('columns', ['tabl2'])

def test_sub_select_suggests_keyword():
    suggestion = suggest_type('SELECT * FROM (', 'SELECT * FROM (')
    assert suggestion == ('keywords', [])

def test_sub_select_partial_text_suggests_keyword():
    suggestion = suggest_type('SELECT * FROM (S', 'SELECT * FROM (S')
    assert suggestion == ('keywords', [])

def test_sub_select_table_name_completion():
    suggestion = suggest_type('SELECT * FROM (SELECT * FROM ',
            'SELECT * FROM (SELECT * FROM ')
    assert suggestion == ('tables', [])

def test_sub_select_col_name_completion():
    suggestion = suggest_type('SELECT * FROM (SELECT  FROM abc',
            'SELECT * FROM (SELECT ')
    assert suggestion == ('columns-and-functions', ['abc'])

@pytest.mark.xfail
def test_sub_select_multiple_col_name_completion():
    suggestion = suggest_type('SELECT * FROM (SELECT a, FROM abc',
            'SELECT * FROM (SELECT a, ')
    assert suggestion == ('columns-and-functions', ['abc'])

def test_sub_select_dot_col_name_completion():
    suggestion = suggest_type('SELECT * FROM (SELECT t. FROM tabl t',
            'SELECT * FROM (SELECT t.')
    assert suggestion == ('columns', ['tabl'])

def test_join_suggests_tables():
    suggestion = suggest_type('SELECT * FROM abc a JOIN ',
            'SELECT * FROM abc a JOIN ')
    assert suggestion == ('tables', [])

def test_join_alias_dot_suggests_cols1():
    suggestion = suggest_type('SELECT * FROM abc a JOIN def d ON a.',
            'SELECT * FROM abc a JOIN def d ON a.')
    assert suggestion == ('columns', ['abc'])

def test_join_alias_dot_suggests_cols2():
    suggestion = suggest_type('SELECT * FROM abc a JOIN def d ON a.',
            'SELECT * FROM abc a JOIN def d ON a.id = d.')
    assert suggestion == ('columns', ['def'])

def test_on_suggests_aliases():
    category, scope = suggest_type(
        'select a.x, b.y from abc a join bcd b on ',
        'select a.x, b.y from abc a join bcd b on ')
    assert category == 'tables-or-aliases'
    assert set(scope) == set(['a', 'b'])

def test_on_suggests_tables():
    category, scope = suggest_type(
        'select abc.x, bcd.y from abc join bcd on ',
        'select abc.x, bcd.y from abc join bcd on ')
    assert category == 'tables-or-aliases'
    assert set(scope) == set(['abc', 'bcd'])
