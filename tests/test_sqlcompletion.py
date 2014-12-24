from pgcli.packages.sqlcompletion import suggest_type


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
    assert suggestion == ('tables', ['tbl1'])

def test_into_suggests_tables():
    suggestion = suggest_type('INSERT INTO ',
            'INSERT INTO ')
    assert suggestion == ('tables', [])

def test_partially_typed_col_name_suggests_col_names():
    suggestion = suggest_type('SELECT * FROM tabl WHERE col_n',
            'SELECT * FROM tabl WHERE col_n')
    assert suggestion == ('columns-and-functions', ['tabl'])
