from __future__ import unicode_literals
import pytest
from metadata import (MetaData, alias, name_join, fk_join, join, keyword,
    table,
    view,
    function,
    column,
    schema,
    datatype,
    wildcard_expansion)
from prompt_toolkit.document import Document
from pgcli.packages.function_metadata import FunctionMetadata, ForeignKey

metadata = {
                'tables': {
                    'users': ['id', 'parentid', 'email', 'first_name', 'last_name'],
                    'Users': ['userid', 'username'],
                    'orders': ['id', 'ordered_date', 'status', 'email'],
                    'select': ['id', 'insert', 'ABC']},
                'views': {
                    'user_emails': ['id', 'email']},
                'functions': [
                    ['custom_func1', [''], [''], [''], '', False, False,
                        False],
                    ['custom_func2', [''], [''], [''], '', False, False,
                        False],
                    ['set_returning_func', ['x', 'y'], ['integer', 'integer'],
                        ['o', 'o'], '', False, False, True]],
                'datatypes': ['custom_type1', 'custom_type2'],
                'foreignkeys': [
                    ('public', 'users', 'id', 'public', 'users', 'parentid'),
                    ('public', 'users', 'id', 'public', 'Users', 'userid')
                ],
            }

metadata = dict((k, {'public': v}) for k, v in metadata.items())

testdata = MetaData(metadata)

@pytest.fixture
def completer():
    return testdata.completer

@pytest.fixture
def complete_event():
    from mock import Mock
    return Mock()

def test_empty_string_completion(completer, complete_event):
    text = ''
    position = 0
    result = set(
        completer.get_completions(
            Document(text=text, cursor_position=position),
            complete_event))
    assert set(testdata.keywords()) == result

def test_select_keyword_completion(completer, complete_event):
    text = 'SEL'
    position = len('SEL')
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert set(result) == set([keyword('SELECT', -3)])


def test_schema_or_visible_table_completion(completer, complete_event):
    text = 'SELECT * FROM '
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        schema('public'),
        table('users'),
        table('"Users"'),
        table('"select"'),
        table('orders'),
        view('user_emails'),
        function('custom_func1'),
        function('custom_func2'),
        function('set_returning_func')])


def test_builtin_function_name_completion(completer, complete_event):
    text = 'SELECT MA'
    position = len('SELECT MA')
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([function('MAX', -2),
                               keyword('MAXEXTENTS', -2),
                              ])


def test_builtin_function_matches_only_at_start(completer, complete_event):
    text = 'SELECT IN'
    position = len('SELECT IN')
    document = Document(text=text, cursor_position=position)

    result = [c.text for c in
              completer.get_completions(document, complete_event)]

    assert 'MIN' not in result


def test_user_function_name_completion(completer, complete_event):
    text = 'SELECT cu'
    position = len('SELECT cu')
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        function('custom_func1', -2),
        function('custom_func2', -2),
        keyword('CURRENT', -2),
        ])


def test_user_function_name_completion_matches_anywhere(completer,
                                                        complete_event):
    text = 'SELECT om'
    position = len('SELECT om')
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        function('custom_func1', -2),
        function('custom_func2', -2)])


def test_suggested_column_names_from_visible_table(completer, complete_event):
    """
    Suggest column and function names when selecting from table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT  from users'
    position = len('SELECT ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        column('id'),
        column('parentid'),
        column('email'),
        column('first_name'),
        column('last_name'),
        function('custom_func1'),
        function('custom_func2'),
    function('set_returning_func')] +
        list(testdata.builtin_functions() +
        testdata.keywords())
        )


def test_suggested_column_names_in_function(completer, complete_event):
    """
    Suggest column and function names when selecting multiple
    columns from table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT MAX( from users'
    position = len('SELECT MAX(')
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert set(result) == set([
        column('id'),
        column('parentid'),
        column('email'),
        column('first_name'),
        column('last_name')])

def test_suggested_column_names_with_table_dot(completer, complete_event):
    """
    Suggest column names on table name and dot
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT users. from users'
    position = len('SELECT users.')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        column('id'),
        column('parentid'),
        column('email'),
        column('first_name'),
        column('last_name')])

def test_suggested_column_names_with_alias(completer, complete_event):
    """
    Suggest column names on table alias and dot
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT u. from users u'
    position = len('SELECT u.')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        column('id'),
        column('parentid'),
        column('email'),
        column('first_name'),
        column('last_name')])

def test_suggested_multiple_column_names(completer, complete_event):
    """
    Suggest column and function names when selecting multiple
    columns from table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT id,  from users u'
    position = len('SELECT id, ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        column('id'),
        column('parentid'),
        column('email'),
        column('first_name'),
        column('last_name'),
        function('custom_func1'),
        function('custom_func2'),
        function('set_returning_func')] +
        list(testdata.builtin_functions() +
        testdata.keywords())
        )

def test_suggested_multiple_column_names_with_alias(completer, complete_event):
    """
    Suggest column names on table alias and dot
    when selecting multiple columns from table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT u.id, u. from users u'
    position = len('SELECT u.id, u.')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        column('id'),
        column('parentid'),
        column('email'),
        column('first_name'),
        column('last_name')])

def test_suggested_multiple_column_names_with_dot(completer, complete_event):
    """
    Suggest column names on table names and dot
    when selecting multiple columns from table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT users.id, users. from users u'
    position = len('SELECT users.id, users.')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        column('id'),
        column('parentid'),
        column('email'),
        column('first_name'),
        column('last_name')])


def test_suggest_columns_after_three_way_join(completer, complete_event):
    text = '''SELECT * FROM users u1
              INNER JOIN users u2 ON u1.id = u2.id
              INNER JOIN users u3 ON u2.id = u3.'''
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert (column('id') in
            set(result))

@pytest.mark.parametrize('text', [
    'SELECT * FROM users u JOIN "Users" u2 ON ',
    'SELECT * FROM users u INNER join "Users" u2 ON ',
    'SELECT * FROM USERS u right JOIN "Users" u2 ON ',
    'SELECT * FROM users u LEFT JOIN "Users" u2 ON ',
    'SELECT * FROM Users u FULL JOIN "Users" u2 ON ',
    'SELECT * FROM users u right outer join "Users" u2 ON ',
    'SELECT * FROM Users u LEFT OUTER JOIN "Users" u2 ON ',
    'SELECT * FROM users u FULL OUTER JOIN "Users" u2 ON ',
    '''SELECT *
    FROM users u
    FULL OUTER JOIN "Users" u2 ON
    '''
])
def test_suggested_join_conditions(completer, complete_event, text):
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        alias('u'),
        alias('u2'),
        fk_join('u2.userid = u.id')])

@pytest.mark.parametrize('text', [
    '''SELECT *
    FROM users
    CROSS JOIN "Users"
    NATURAL JOIN users u
    JOIN "Users" u2 ON
    '''
])
def test_suggested_join_conditions_with_same_table_twice(completer, complete_event, text):
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert result == [
        fk_join('u2.userid = u.id'),
        fk_join('u2.userid = users.id'),
        name_join('u2.userid = "Users".userid'),
        name_join('u2.username = "Users".username'),
        alias('"Users"'),
        alias('u'),
        alias('u2'),
        alias('users')]

@pytest.mark.parametrize('text', [
    'SELECT * FROM users JOIN users u2 on foo.'
])
def test_suggested_join_conditions_with_invalid_qualifier(completer, complete_event, text):
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set()

@pytest.mark.parametrize(('text', 'ref'), [
    ('SELECT * FROM users JOIN NonTable on ', 'NonTable'),
    ('SELECT * FROM users JOIN nontable nt on ', 'nt')
])
def test_suggested_join_conditions_with_invalid_table(completer, complete_event, text, ref):
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([alias('users'), alias(ref)])

@pytest.mark.parametrize('text', [
    'SELECT * FROM "Users" u JOIN u',
    'SELECT * FROM "Users" u JOIN uid',
    'SELECT * FROM "Users" u JOIN userid',
    'SELECT * FROM "Users" u JOIN id',
])
def test_suggested_joins_fuzzy(completer, complete_event, text):
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    last_word = text.split()[-1]
    expected = join('users ON users.id = u.userid', -len(last_word))
    assert expected in result

@pytest.mark.parametrize('text', [
    'SELECT * FROM users JOIN ',
    '''SELECT *
    FROM users
    INNER JOIN '''
])
def test_suggested_joins(completer, complete_event, text):
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        schema('public'),
        join('"Users" ON "Users".userid = users.id'),
        join('users users2 ON users2.id = users.parentid'),
        join('users users2 ON users2.parentid = users.id'),
        table('"Users"'),
        table('"select"'),
        table('orders'),
        table('users'),
        view('user_emails'),
        function('custom_func2'),
        function('set_returning_func'),
        function('custom_func1')])

@pytest.mark.parametrize('text', [
    'SELECT * FROM public."Users" JOIN ',
    'SELECT * FROM public."Users" RIGHT OUTER JOIN ',
    '''SELECT *
    FROM public."Users"
    LEFT JOIN '''
])
def test_suggested_joins_quoted_schema_qualified_table(completer, complete_event, text):
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        join('public.users ON users.id = "Users".userid'),
        schema('public'),
        table('"Users"'),
        table('"select"'),
        table('orders'),
        table('users'),
        view('user_emails'),
        function('custom_func2'),
        function('set_returning_func'),
        function('custom_func1')])

@pytest.mark.parametrize('text', [
    'SELECT u.name, o.id FROM users u JOIN orders o ON ',
    'SELECT u.name, o.id FROM users u JOIN orders o ON JOIN orders o2 ON'
])
def test_suggested_aliases_after_on(completer, complete_event, text):
    position = len('SELECT u.name, o.id FROM users u JOIN orders o ON ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        alias('u'),
        name_join('o.id = u.id'),
        name_join('o.email = u.email'),
        alias('o')])

@pytest.mark.parametrize('text', [
    'SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = ',
    'SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id =  JOIN orders o2 ON'
])
def test_suggested_aliases_after_on_right_side(completer, complete_event, text):
    position = len('SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        alias('u'),
        alias('o')])

@pytest.mark.parametrize('text', [
    'SELECT users.name, orders.id FROM users JOIN orders ON ',
    'SELECT users.name, orders.id FROM users JOIN orders ON JOIN orders orders2 ON'
])
def test_suggested_tables_after_on(completer, complete_event, text):
    position = len('SELECT users.name, orders.id FROM users JOIN orders ON ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        name_join('orders.id = users.id'),
        name_join('orders.email = users.email'),
        alias('users'),
        alias('orders')])

@pytest.mark.parametrize('text', [
    'SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = JOIN orders orders2 ON',
    'SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = '
])
def test_suggested_tables_after_on_right_side(completer, complete_event, text):
    position = len('SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        alias('users'),
        alias('orders')])

@pytest.mark.parametrize('text', [
    'SELECT * FROM users INNER JOIN orders USING (',
    'SELECT * FROM users INNER JOIN orders USING(',
])
def test_join_using_suggests_common_columns(completer, complete_event, text):
    pos = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set([
        column('id'),
        column('email'),
        ])

@pytest.mark.parametrize('text', [
    'SELECT * FROM users u1 JOIN users u2 USING (email) JOIN user_emails ue USING()',
    'SELECT * FROM users u1 JOIN users u2 USING(email) JOIN user_emails ue USING ()',
    'SELECT * FROM users u1 JOIN user_emails ue USING () JOIN users u2 ue USING(first_name, last_name)',
    'SELECT * FROM users u1 JOIN user_emails ue USING() JOIN users u2 ue USING (first_name, last_name)',
])
def test_join_using_suggests_from_last_table(completer, complete_event, text):
    pos = text.index('()') + 1
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set([
        column('id'),
        column('email'),
        ])

@pytest.mark.parametrize('text', [
    'SELECT * FROM users INNER JOIN orders USING (id,',
    'SELECT * FROM users INNER JOIN orders USING(id,',
])
def test_join_using_suggests_columns_after_first_column(completer, complete_event, text):
    pos = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set([
        column('id'),
        column('email'),
        ])

@pytest.mark.parametrize('text', [
    'SELECT * FROM ',
    'SELECT * FROM users CROSS JOIN ',
    'SELECT * FROM users natural join '
])
def test_table_names_after_from(completer, complete_event, text):
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert set(result) == set([
        schema('public'),
        table('users'),
        table('"Users"'),
        table('orders'),
        table('"select"'),
        view('user_emails'),
        function('custom_func1'),
        function('custom_func2'),
        function('set_returning_func')
        ])
    assert [c.text for c in result] == [
        '"Users"',
        'custom_func1',
        'custom_func2',
        'orders',
        'public',
        '"select"',
        'set_returning_func',
        'user_emails',
        'users'
        ]

def test_auto_escaped_col_names(completer, complete_event):
    text = 'SELECT  from "select"'
    position = len('SELECT ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        column('id'),
        column('"insert"'),
        column('"ABC"'),
        function('custom_func1'),
        function('custom_func2'),
        function('set_returning_func')] +
        list(testdata.builtin_functions() +
        testdata.keywords())
        )


def test_allow_leading_double_quote_in_last_word(completer, complete_event):
    text = 'SELECT * from "sele'
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)

    expected = table('"select"', -5)

    assert expected in set(result)


@pytest.mark.parametrize('text', [
    'SELECT 1::',
    'CREATE TABLE foo (bar ',
    'CREATE FUNCTION foo (bar INT, baz ',
    'ALTER TABLE foo ALTER COLUMN bar TYPE ',
])
def test_suggest_datatype(text, completer, complete_event):
    pos = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event)
    assert set(result) == set([
        schema('public'),
        datatype('custom_type1'),
        datatype('custom_type2'),
        table('users'),
        table('"Users"'),
        table('orders'),
        table('"select"')] +
        list(testdata.builtin_datatypes()))


def test_suggest_columns_from_escaped_table_alias(completer, complete_event):
    sql = 'select * from "select" s where s.'
    pos = len(sql)
    result = completer.get_completions(Document(text=sql, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        column('id'),
        column('"insert"'),
        column('"ABC"'),
    ])


def test_suggest_columns_from_set_returning_function(completer, complete_event):
    sql = 'select  from set_returning_func()'
    pos = len('select ')
    result = completer.get_completions(Document(text=sql, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        column('x'),
        column('y'),
        function('custom_func1'),
        function('custom_func2'),
        function('set_returning_func')]
         + list(testdata.builtin_functions()
         + testdata.keywords()))


def test_suggest_columns_from_aliased_set_returning_function(completer, complete_event):
    sql = 'select f. from set_returning_func() f'
    pos = len('select f.')
    result = completer.get_completions(Document(text=sql, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        column('x'),
        column('y')])


def test_join_functions_using_suggests_common_columns(completer, complete_event):
    text = '''SELECT * FROM set_returning_func() f1
              INNER JOIN set_returning_func() f2 USING ('''
    pos = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set([
         column('x'),
         column('y')])


def test_join_functions_on_suggests_columns_and_join_conditions(completer, complete_event):
    text = '''SELECT * FROM set_returning_func() f1
              INNER JOIN set_returning_func() f2 ON f1.'''
    pos = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set([
         name_join('y = f2.y'),
         name_join('x = f2.x'),
         column('x'),
         column('y')])


def test_learn_keywords(completer, complete_event):
    sql = 'CREATE VIEW v AS SELECT 1'
    completer.extend_query_history(sql)

    # Now that we've used `VIEW` once, it should be suggested ahead of other
    # keywords starting with v.
    sql = 'create v'
    completions = completer.get_completions(
        Document(text=sql, cursor_position=len(sql)), complete_event)
    assert completions[0].text == 'VIEW'


def test_learn_table_names(completer, complete_event):
    history = 'SELECT * FROM users; SELECT * FROM orders; SELECT * FROM users'
    completer.extend_query_history(history)

    sql = 'SELECT * FROM '
    completions = completer.get_completions(
        Document(text=sql, cursor_position=len(sql)), complete_event)

    # `users` should be higher priority than `orders` (used more often)
    users = table('users')
    orders = table('orders')

    assert completions.index(users) < completions.index(orders)


def test_columns_before_keywords(completer, complete_event):
    sql = 'SELECT * FROM orders WHERE s'
    completions = completer.get_completions(
        Document(text=sql, cursor_position=len(sql)), complete_event)

    col = column('status', -1)
    kw = keyword('SELECT', -1)

    assert completions.index(col) < completions.index(kw)


def test_wildcard_column_expansion(completer, complete_event):
    sql = 'SELECT * FROM users'
    pos = len('SELECT *')

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, parentid, email, first_name, last_name'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


def test_wildcard_column_expansion_with_alias_qualifier(completer, complete_event):
    sql = 'SELECT u.* FROM users u'
    pos = len('SELECT u.*')

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, u.parentid, u.email, u.first_name, u.last_name'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions

@pytest.mark.parametrize('text,expected', [
    ('SELECT users.* FROM users',
        'id, users.parentid, users.email, users.first_name, users.last_name'),
    ('SELECT Users.* FROM Users',
        'id, Users.parentid, Users.email, Users.first_name, Users.last_name'),
])
def test_wildcard_column_expansion_with_table_qualifier(completer, complete_event, text, expected):
    pos = len('SELECT users.*')

    completions = completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event)

    expected = [wildcard_expansion(expected)]

    assert expected == completions

def test_wildcard_column_expansion_with_two_tables(completer, complete_event):
    sql = 'SELECT * FROM "select" JOIN users u ON true'
    pos = len('SELECT *')

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    cols = ('"select".id, "select"."insert", "select"."ABC", '
        'u.id, u.parentid, u.email, u.first_name, u.last_name')
    expected = [wildcard_expansion(cols)]
    assert completions == expected


def test_wildcard_column_expansion_with_two_tables_and_parent(completer, complete_event):
    sql = 'SELECT "select".* FROM "select" JOIN users u ON true'
    pos = len('SELECT "select".*')

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, "select"."insert", "select"."ABC"'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@pytest.mark.parametrize('text', [
    'SELECT U. FROM Users U',
    'SELECT U. FROM USERS U',
    'SELECT U. FROM users U'
])
def test_suggest_columns_from_unquoted_table(completer, complete_event, text):
    pos = len('SELECT U.')
    result = completer.get_completions(Document(text=text, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        column('id'),
        column('parentid'),
        column('email'),
        column('first_name'),
        column('last_name')])


def test_suggest_columns_from_quoted_table(completer, complete_event):
    text = 'SELECT U. FROM "Users" U'
    pos = len('SELECT U.')
    result = completer.get_completions(Document(text=text, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        column('userid'),
        column('username')])
