from pgcli.packages.sqlcompletion import suggest_type
import pytest

def test_select_suggests_cols_with_visible_table_scope():
    suggestions = suggest_type('SELECT  FROM tabl', 'SELECT ')
    assert sorted(suggestions) == sorted([
            {'type': 'column', 'tables': [(None, 'tabl', None)]},
            {'type': 'function'}])

def test_select_suggests_cols_with_qualified_table_scope():
    suggestions = suggest_type('SELECT  FROM sch.tabl', 'SELECT ')
    assert sorted(suggestions) == sorted([
            {'type': 'column', 'tables': [('sch', 'tabl', None)]},
            {'type': 'function'}])

def test_where_suggests_columns_functions():
    suggestions = suggest_type('SELECT * FROM tabl WHERE ',
            'SELECT * FROM tabl WHERE ')
    assert sorted(suggestions) == sorted([
            {'type': 'column', 'tables': [(None, 'tabl', None)]},
            {'type': 'function'}])

def test_lparen_suggests_cols():
    suggestion = suggest_type('SELECT MAX( FROM tbl', 'SELECT MAX(')
    assert suggestion == [
        {'type': 'column', 'tables': [(None, 'tbl', None)]}]

def test_select_suggests_cols_and_funcs():
    suggestions = suggest_type('SELECT ', 'SELECT ')
    assert sorted(suggestions) == sorted([
         {'type': 'column', 'tables': []},
         {'type': 'function'}])

def test_from_suggests_tables_and_schemas():
    suggestions = suggest_type('SELECT * FROM ', 'SELECT * FROM ')
    assert sorted(suggestions) == sorted([
        {'type': 'table', 'schema': []},
        {'type': 'schema'}])

def test_distinct_suggests_cols():
    suggestions = suggest_type('SELECT DISTINCT ', 'SELECT DISTINCT ')
    assert suggestions == [{'type': 'column', 'tables': []}]

def test_col_comma_suggests_cols():
    suggestions = suggest_type('SELECT a, b, FROM tbl', 'SELECT a, b,')
    assert sorted(suggestions) == sorted([
        {'type': 'column', 'tables': [(None, 'tbl', None)]},
         {'type': 'function'}])

def test_table_comma_suggests_tables_and_schemas():
    suggestions = suggest_type('SELECT a, b FROM tbl1, ',
            'SELECT a, b FROM tbl1, ')
    assert sorted(suggestions) == sorted([
        {'type': 'table', 'schema': []},
        {'type': 'schema'}])

def test_into_suggests_tables_and_schemas():
    suggestion = suggest_type('INSERT INTO ', 'INSERT INTO ')
    assert sorted(suggestion) == sorted([
        {'type': 'table', 'schema': []},
        {'type': 'schema'}])

def test_insert_into_lparen_suggests_cols():
    suggestions = suggest_type('INSERT INTO abc (', 'INSERT INTO abc (')
    assert suggestions == [{'type': 'column', 'tables': [(None, 'abc', None)]}]

def test_insert_into_lparen_partial_text_suggests_cols():
    suggestions = suggest_type('INSERT INTO abc (i', 'INSERT INTO abc (i')
    assert suggestions == [{'type': 'column', 'tables': [(None, 'abc', None)]}]

def test_insert_into_lparen_comma_suggests_cols():
    suggestions = suggest_type('INSERT INTO abc (id,', 'INSERT INTO abc (id,')
    assert suggestions == [{'type': 'column', 'tables': [(None, 'abc', None)]}]

def test_partially_typed_col_name_suggests_col_names():
    suggestions = suggest_type('SELECT * FROM tabl WHERE col_n',
            'SELECT * FROM tabl WHERE col_n')
    assert sorted(suggestions) == sorted([
        {'type': 'column', 'tables': [(None, 'tabl', None)]},
        {'type': 'function'}])

def test_dot_suggests_cols_of_a_table_or_schema_qualified_table():
    suggestions = suggest_type('SELECT tabl. FROM tabl', 'SELECT tabl.')
    assert sorted(suggestions) == sorted([
        {'type': 'column', 'tables': [(None, 'tabl', None)]},
        {'type': 'table', 'schema': 'tabl'}])

def test_dot_suggests_cols_of_an_alias():
    suggestions = suggest_type('SELECT t1. FROM tabl1 t1, tabl2 t2',
            'SELECT t1.')
    assert sorted(suggestions) == sorted([
        {'type': 'table', 'schema': 't1'},
        {'type': 'column', 'tables': [(None, 'tabl1', 't1')]}])

def test_dot_col_comma_suggests_cols_or_schema_qualified_table():
    suggestions = suggest_type('SELECT t1.a, t2. FROM tabl1 t1, tabl2 t2',
            'SELECT t1.a, t2.')
    assert sorted(suggestions) == sorted([
        {'type': 'column', 'tables': [(None, 'tabl2', 't2')]},
        {'type': 'table', 'schema': 't2'}])

def test_sub_select_suggests_keyword():
    suggestion = suggest_type('SELECT * FROM (', 'SELECT * FROM (')
    assert suggestion == [{'type': 'keyword'}]

def test_sub_select_partial_text_suggests_keyword():
    suggestion = suggest_type('SELECT * FROM (S', 'SELECT * FROM (S')
    assert suggestion == [{'type': 'keyword'}]

def test_sub_select_table_name_completion():
    suggestion = suggest_type('SELECT * FROM (SELECT * FROM ',
            'SELECT * FROM (SELECT * FROM ')
    assert sorted(suggestion) == sorted([
        {'type': 'table', 'schema': []}, {'type': 'schema'}])

def test_sub_select_col_name_completion():
    suggestions = suggest_type('SELECT * FROM (SELECT  FROM abc',
            'SELECT * FROM (SELECT ')
    assert sorted(suggestions) == sorted([
        {'type': 'column', 'tables': [(None, 'abc', None)]},
        {'type': 'function'}])

@pytest.mark.xfail
def test_sub_select_multiple_col_name_completion():
    suggestions = suggest_type('SELECT * FROM (SELECT a, FROM abc',
            'SELECT * FROM (SELECT a, ')
    assert sorted(suggestions) == sorted([
        {'type': 'column', 'tables': [(None, 'abc', None)]},
        {'type': 'function'}])

def test_sub_select_dot_col_name_completion():
    suggestions = suggest_type('SELECT * FROM (SELECT t. FROM tabl t',
            'SELECT * FROM (SELECT t.')
    assert sorted(suggestions) == sorted([
        {'type': 'column', 'tables': [(None, 'tabl', 't')]},
        {'type': 'table', 'schema': 't'}])

def test_join_suggests_tables_and_schemas():
    suggestion = suggest_type('SELECT * FROM abc a JOIN ',
            'SELECT * FROM abc a JOIN ')
    assert sorted(suggestion) == sorted([
        {'type': 'table', 'schema': []},
        {'type': 'schema'}])

def test_join_alias_dot_suggests_cols1():
    suggestions = suggest_type('SELECT * FROM abc a JOIN def d ON a.',
            'SELECT * FROM abc a JOIN def d ON a.')
    assert sorted(suggestions) == sorted([
        {'type': 'column', 'tables': [(None, 'abc', 'a')]},
        {'type': 'table', 'schema': 'a'}])

def test_join_alias_dot_suggests_cols2():
    suggestion = suggest_type('SELECT * FROM abc a JOIN def d ON a.',
            'SELECT * FROM abc a JOIN def d ON a.id = d.')
    assert sorted(suggestion) == sorted([
        {'type': 'column', 'tables': [(None, 'def', 'd')]},
        {'type': 'table', 'schema': 'd'}])

def test_on_suggests_aliases():
    suggestions = suggest_type(
        'select a.x, b.y from abc a join bcd b on ',
        'select a.x, b.y from abc a join bcd b on ')
    assert suggestions == [{'type': 'alias', 'aliases': ['a', 'b']}]

def test_on_suggests_tables():
    suggestions = suggest_type(
        'select abc.x, bcd.y from abc join bcd on ',
        'select abc.x, bcd.y from abc join bcd on ')
    assert suggestions == [{'type': 'alias', 'aliases': ['abc', 'bcd']}]
    
def test_on_suggests_aliases_right_side():
    suggestions = suggest_type(
        'select a.x, b.y from abc a join bcd b on a.id = ',
        'select a.x, b.y from abc a join bcd b on a.id = ')
    assert suggestions == [{'type': 'alias', 'aliases': ['a', 'b']}]
        
def test_on_suggests_tables_right_side():
    suggestions = suggest_type(
        'select abc.x, bcd.y from abc join bcd on ',
        'select abc.x, bcd.y from abc join bcd on ')
    assert suggestions == [{'type': 'alias', 'aliases': ['abc', 'bcd']}]
