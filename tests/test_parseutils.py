from pgcli.packages.parseutils import extract_tables

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
    import pdb; pdb.set_trace()
    tables = extract_tables('update abc set id = 1')
    assert tables == ['abc']
