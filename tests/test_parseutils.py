from pgcli.packages.parseutils import extract_tables


def test_empty_string():
    tables = extract_tables('')
    assert tables == []

def test_simple_select_single_table():
    tables = extract_tables('select * from abc')
    assert tables == ['abc']

def test_simple_select_multiple_tables():
    tables = extract_tables('select * from abc, def')
    assert tables == ['abc', 'def']

def test_simple_select_with_cols_single_table():
    tables = extract_tables('select a,b from abc')
    assert tables == ['abc']

def test_simple_select_with_cols_multiple_tables():
    tables = extract_tables('select a,b from abc, def')
    assert tables == ['abc', 'def']

def test_select_with_hanging_comma_single_table():
    tables = extract_tables('select a, from abc')
    assert tables == ['abc']

def test_select_with_hanging_comma_multiple_tables():
    tables = extract_tables('select a, from abc, def')
    assert tables == ['abc', 'def']

def test_simple_insert_single_table():
    tables = extract_tables('insert into abc (id, name) values (1, "def")')
    assert tables == ['abc']

def test_simple_update_table():
    tables = extract_tables('update abc set id = 1')
    assert tables == ['abc']

def test_join_table():
    expected = {'a': 'abc', 'd': 'def'}
    tables = extract_tables('SELECT * FROM abc a JOIN def d ON a.id = d.num')
    tables_aliases = extract_tables(
            'SELECT * FROM abc a JOIN def d ON a.id = d.num', True)
    assert tables == expected.values()
    assert tables_aliases == expected

def test_join_as_table():
    expected = {'m': 'my_table'}
    assert extract_tables(
            'SELECT * FROM my_table AS m WHERE m.a > 5') == expected.values()
    assert extract_tables(
            'SELECT * FROM my_table AS m WHERE m.a > 5', True) == expected
