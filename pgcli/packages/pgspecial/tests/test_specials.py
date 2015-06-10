from dbutils import dbtest

@dbtest
def test_slash_d(executor):
    results = executor('\d')
    title = None
    rows = [('public', 'tbl1', 'table', 'postgres'),
            ('public', 'tbl2', 'table', 'postgres'),
            ('public', 'vw1', 'view', 'postgres')]
    headers = ['Schema', 'Name', 'Type', 'Owner']
    status = 'SELECT 3'
    expected = [title, rows, headers, status]
    assert results == expected

@dbtest
def test_slash_dn(executor):
    """List all schemas."""
    results = executor('\dn')
    title = None
    rows = [('public', 'postgres'),
            ('schema1', 'postgres'),
            ('schema2', 'postgres')]
    headers = ['Name', 'Owner']
    status = 'SELECT 3'
    expected = [title, rows, headers, status]
    assert results == expected

@dbtest
def test_slash_dt(executor):
    """List all tables in public schema."""
    results = executor('\dt')
    title = None
    rows = [('public', 'tbl1', 'table', 'postgres'),
            ('public', 'tbl2', 'table', 'postgres')]
    headers = ['Schema', 'Name', 'Type', 'Owner']
    status = 'SELECT 2'
    expected = [title, rows, headers, status]
    assert results == expected

@dbtest
def test_slash_dT(executor):
    """List all datatypes."""
    results = executor('\dT')
    title = None
    rows = [('public', 'foo', None)]
    headers = ['Schema', 'Name', 'Description']
    status = 'SELECT 1'
    expected = [title, rows, headers, status]
    assert results == expected

@dbtest
def test_slash_df(executor):
    results = executor('\df')
    title = None
    rows = [('public', 'func1', 'integer', '', 'normal')]
    headers = ['Schema', 'Name', 'Result data type', 'Argument data types',
            'Type']
    status = 'SELECT 1'
    expected = [title, rows, headers, status]
    assert results == expected
