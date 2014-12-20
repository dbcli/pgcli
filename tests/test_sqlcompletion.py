from pgcli.packages.sqlcompletion import suggest_type


def test_select_suggests_cols_with_table_scope():
    suggestion = suggest_type('SELECT  FROM tabl', 'SELECT ')
    assert suggestion == ('columns-and-functions', ['tabl'])

def test_lparen_suggest_cols():
    suggestion = suggest_type('SELECT MAX( FROM tbl', 'SELECT MAX(')
    assert suggestion == ('columns', ['tbl'])

def test_select_suggest_cols_and_funcs():
    suggestion = suggest_type('SELECT ', 'SELECT ')
    assert suggestion == ('columns-and-functions', [])

def test_from_suggest_tables():
    suggestion = suggest_type('SELECT * FROM ', 'SELECT * FROM ')
    assert suggestion == ('tables', [])

def test_distinct_suggest_cols():
    suggestion = suggest_type('SELECT DISTINCT ', 'SELECT DISTINCT ')
    assert suggestion == ('columns', [])

def test_multiple_cols_suggest_cols():
    suggestion = suggest_type('SELECT a, b, FROM tbl', 'SELECT a, b,')
    assert suggestion == ('columns-and-functions', ['tbl'])

def test_multiple_tables_suggest_tables():
    suggestion = suggest_type('SELECT a, b FROM tbl1, ',
            'SELECT a, b FROM tbl1, ')
    assert suggestion == ('tables', [])
