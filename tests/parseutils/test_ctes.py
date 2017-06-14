import pytest
from sqlparse import parse
from pgcli.packages.parseutils.ctes import (
    token_start_pos, extract_ctes,
    extract_column_names as _extract_column_names)


def extract_column_names(sql):
    p = parse(sql)[0]
    return _extract_column_names(p)


def test_token_str_pos():
    sql = 'SELECT * FROM xxx'
    p = parse(sql)[0]
    idx = p.token_index(p.tokens[-1])
    assert token_start_pos(p.tokens, idx) == len('SELECT * FROM ')

    sql = 'SELECT * FROM \nxxx'
    p = parse(sql)[0]
    idx = p.token_index(p.tokens[-1])
    assert token_start_pos(p.tokens, idx) == len('SELECT * FROM \n')


def test_single_column_name_extraction():
    sql = 'SELECT abc FROM xxx'
    assert extract_column_names(sql) == ('abc',)


def test_aliased_single_column_name_extraction():
    sql = 'SELECT abc def FROM xxx'
    assert extract_column_names(sql) == ('def',)


def test_aliased_expression_name_extraction():
    sql = 'SELECT 99 abc FROM xxx'
    assert extract_column_names(sql) == ('abc',)


def test_multiple_column_name_extraction():
    sql = 'SELECT abc, def FROM xxx'
    assert extract_column_names(sql) == ('abc', 'def')


def test_missing_column_name_handled_gracefully():
    sql = 'SELECT abc, 99 FROM xxx'
    assert extract_column_names(sql) == ('abc',)

    sql = 'SELECT abc, 99, def FROM xxx'
    assert extract_column_names(sql) == ('abc', 'def')


def test_aliased_multiple_column_name_extraction():
    sql = 'SELECT abc def, ghi jkl FROM xxx'
    assert extract_column_names(sql) == ('def', 'jkl')


def test_table_qualified_column_name_extraction():
    sql = 'SELECT abc.def, ghi.jkl FROM xxx'
    assert extract_column_names(sql) == ('def', 'jkl')


@pytest.mark.parametrize('sql', [
    'INSERT INTO foo (x, y, z) VALUES (5, 6, 7) RETURNING x, y',
    'DELETE FROM foo WHERE x > y RETURNING x, y',
    'UPDATE foo SET x = 9 RETURNING x, y',
])
def test_extract_column_names_from_returning_clause(sql):
    assert extract_column_names(sql) == ('x', 'y')


def test_simple_cte_extraction():
    sql = 'WITH a AS (SELECT abc FROM xxx) SELECT * FROM a'
    start_pos = len('WITH a AS ')
    stop_pos = len('WITH a AS (SELECT abc FROM xxx)')
    ctes, remainder = extract_ctes(sql)

    assert tuple(ctes) == (('a', ('abc',), start_pos, stop_pos),)
    assert remainder.strip() == 'SELECT * FROM a'


def test_cte_extraction_around_comments():
    sql = '''--blah blah blah
            WITH a AS (SELECT abc def FROM x)
            SELECT * FROM a'''
    start_pos = len('''--blah blah blah
            WITH a AS ''')
    stop_pos = len('''--blah blah blah
            WITH a AS (SELECT abc def FROM x)''')

    ctes, remainder = extract_ctes(sql)
    assert tuple(ctes) == (('a', ('def',), start_pos, stop_pos),)
    assert remainder.strip() == 'SELECT * FROM a'


def test_multiple_cte_extraction():
    sql = '''WITH
            x AS (SELECT abc, def FROM x),
            y AS (SELECT ghi, jkl FROM y)
            SELECT * FROM a, b'''

    start1 = len('''WITH
            x AS ''')

    stop1 = len('''WITH
            x AS (SELECT abc, def FROM x)''')

    start2 = len('''WITH
            x AS (SELECT abc, def FROM x),
            y AS ''')

    stop2 = len('''WITH
            x AS (SELECT abc, def FROM x),
            y AS (SELECT ghi, jkl FROM y)''')

    ctes, remainder = extract_ctes(sql)
    assert tuple(ctes) == (
        ('x', ('abc', 'def'), start1, stop1),
        ('y', ('ghi', 'jkl'), start2, stop2))
