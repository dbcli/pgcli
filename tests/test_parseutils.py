import pytest
from pgcli.packages.parseutils import extract_tables


def test_empty_string():
    tables = extract_tables('')
    assert tables.to_dict('list') == {'schema': [], 'table': [], 'alias': []}

def test_simple_select_single_table():
    tables = extract_tables('select * from abc')
    assert tables.to_dict('list') == \
           {'schema': [None], 'table': ['abc'], 'alias': [None]}

def test_simple_select_single_table_schema_qualified():
    tables = extract_tables('select * from abc.def')
    assert tables.to_dict('list') == \
           {'schema': ['abc'], 'table': ['def'], 'alias': [None]}

def test_simple_select_multiple_tables():
    tables = extract_tables('select * from abc, def')
    assert tables.to_dict('list') == \
           {'schema': [None, None],
            'table': ['abc', 'def'],
            'alias': [None, None]}

def test_simple_select_multiple_tables_schema_qualified():
    tables = extract_tables('select * from abc.def, ghi.jkl')
    assert tables.to_dict('list') == \
           {'schema': ['abc', 'ghi'],
            'table': ['def', 'jkl'],
            'alias': [None, None]}

def test_simple_select_with_cols_single_table():
    tables = extract_tables('select a,b from abc')
    assert tables.to_dict('list') == \
           {'schema': [None], 'table': ['abc'], 'alias': [None]}

def test_simple_select_with_cols_single_table_schema_qualified():
    tables = extract_tables('select a,b from abc.def')
    assert tables.to_dict('list') == \
           {'schema': ['abc'], 'table': ['def'], 'alias': [None]}

def test_simple_select_with_cols_multiple_tables():
    tables = extract_tables('select a,b from abc, def')
    assert tables.to_dict('list') == \
           {'schema': [None, None],
            'table': ['abc', 'def'],
            'alias': [None, None]}

def test_simple_select_with_cols_multiple_tables():
    tables = extract_tables('select a,b from abc.def, def.ghi')
    assert tables.to_dict('list') == \
           {'schema': ['abc', 'def'],
            'table': ['def', 'ghi'],
            'alias': [None, None]}

def test_select_with_hanging_comma_single_table():
    tables = extract_tables('select a, from abc')
    assert tables.to_dict('list') == \
           {'schema': [None],
            'table': ['abc'],
            'alias': [None]}

def test_select_with_hanging_comma_multiple_tables():
    tables = extract_tables('select a, from abc, def')
    assert tables.to_dict('list') == \
           {'schema': [None, None],
            'table': ['abc', 'def'],
            'alias': [None, None]}

def test_select_with_hanging_period_multiple_tables():
    tables = extract_tables('SELECT t1. FROM tabl1 t1, tabl2 t2')
    assert tables.to_dict('list') == \
           {'schema': [None, None],
            'table': ['tabl1', 'tabl2'],
            'alias': ['t1', 't2']}

def test_simple_insert_single_table():
    tables = extract_tables('insert into abc (id, name) values (1, "def")')
    assert tables.to_dict('list') == \
           {'schema': [None], 'table': ['abc'], 'alias': ['abc']}

@pytest.mark.xfail
def test_simple_insert_single_table_schema_qualified():
    tables = extract_tables('insert into abc.def (id, name) values (1, "def")')
    assert tables.to_dict('list') == \
           {'schema': ['abc'], 'table': ['def'], 'alias': [None]}

def test_simple_update_table():
    tables = extract_tables('update abc set id = 1')
    assert tables.to_dict('list') == \
           {'schema': [None], 'table': ['abc'], 'alias': [None]}

def test_simple_update_table():
    tables = extract_tables('update abc.def set id = 1')
    assert tables.to_dict('list') == \
           {'schema': ['abc'], 'table': ['def'], 'alias': [None]}

def test_join_table():
    tables = extract_tables('SELECT * FROM abc a JOIN def d ON a.id = d.num')
    assert tables.to_dict('list') == \
           {'schema': [None, None],
            'table': ['abc', 'def'],
            'alias': ['a', 'd']}

def test_join_table_schema_qualified():
    tables = extract_tables('SELECT * FROM abc.def x JOIN ghi.jkl y ON x.id = y.num')
    assert tables.to_dict('list') == \
           {'schema': ['abc', 'ghi'],
            'table': ['def', 'jkl'],
            'alias': ['x', 'y']}

def test_join_as_table():
    tables = extract_tables('SELECT * FROM my_table AS m WHERE m.a > 5')
    assert tables.to_dict('list') == \
           {'schema': [None], 'table': ['my_table'], 'alias': ['m']}

