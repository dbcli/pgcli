from __future__ import unicode_literals
import pytest
from metadata import (MetaData, alias, name_join, fk_join, join, keyword,
    schema, table, view, function, column, wildcard_expansion)
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion

metadata = {
    'tables': {
        'users': ['id', 'parentid', 'email', 'first_name', 'last_name'],
        'Users': ['userid', 'username'],
        'orders': ['id', 'ordered_date', 'status', 'email'],
        'select': ['id', 'insert', 'ABC']},
    'views': {
        'user_emails': ['id', 'email']},
    'functions': [
        ['custom_fun', [''], [''], [''], '', False, False, False],
        ['_custom_fun', [''], [''], [''], '', False, False, False],
        ['custom_func1', [''], [''], [''], '', False, False, False],
        ['custom_func2', [''], [''], [''], '', False, False, False],
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

cased_users_col_names = ['ID', 'PARENTID', 'Email', 'First_Name', 'last_name']
cased_users2_col_names = ['UserID', 'UserName']
cased_funcs = ['Custom_Fun', '_custom_fun', 'Custom_Func1',
    'custom_func2', 'set_returning_func']
cased_tbls = ['Users', 'Orders']
cased_views = ['User_Emails']
casing =  (['SELECT', 'PUBLIC'] + cased_funcs + cased_tbls + cased_views
    + cased_users_col_names + cased_users2_col_names)
# Lists for use in assertions
cased_funcs = [function(f + '()') for f in cased_funcs]
cased_tbls = [table(t) for t in (cased_tbls + ['"Users"', '"select"'])]
cased_rels = [view(t) for t in cased_views] + cased_funcs + cased_tbls
cased_users_cols = [column(c) for c in cased_users_col_names]
aliased_rels = [table(t) for t in ('users u', '"Users" U', 'orders o',
    '"select" s')] + [view('user_emails ue')] + [function(f) for f in (
    '_custom_fun() cf', 'custom_fun() cf', 'custom_func1() cf',
    'custom_func2() cf', 'set_returning_func() srf')]
cased_aliased_rels = [table(t) for t in ('Users U', '"Users" U', 'Orders O',
    '"select" s')] + [view('User_Emails UE')] + [function(f) for f in (
    '_custom_fun() cf', 'Custom_Fun() CF', 'Custom_Func1() CF',
    'custom_func2() cf', 'set_returning_func() srf')]


@pytest.fixture
def completer():
    return testdata.completer

@pytest.fixture
def cased_completer():
    return testdata.get_completer(casing=casing)

@pytest.fixture
def aliased_completer():
    return testdata.get_completer({'generate_aliases': True})

@pytest.fixture
def cased_aliased_completer():
    return testdata.get_completer({'generate_aliases': True}, casing)

@pytest.fixture
def cased_always_qualifying_completer():
    return testdata.get_completer({'qualify_columns': 'always'}, casing)

@pytest.fixture
def auto_qualifying_completer():
    return testdata.get_completer({'qualify_columns': 'if_more_than_one_table'})


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
        function('custom_fun()', -2),
        function('_custom_fun()', -2),
        function('custom_func1()', -2),
        function('custom_func2()', -2),
        keyword('CURRENT', -2),
        ])


def test_user_function_name_completion_matches_anywhere(completer,
                                                        complete_event):
    text = 'SELECT om'
    position = len('SELECT om')
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        function('custom_fun()', -2),
        function('_custom_fun()', -2),
        function('custom_func1()', -2),
        function('custom_func2()', -2)])


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
    assert set(result) == set(testdata.columns('users') + testdata.functions() +
        list(testdata.builtin_functions() +
        testdata.keywords())
        )


def test_suggested_cased_column_names(cased_completer, complete_event):
    """
    Suggest column and function names when selecting from table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT  from users'
    position = len('SELECT ')
    result = set(cased_completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(cased_funcs + cased_users_cols
        + testdata.builtin_functions() + testdata.keywords())


@pytest.mark.parametrize('text', [
    'SELECT  from users',
    'INSERT INTO Orders SELECT  from users',
])
def test_suggested_auto_qualified_column_names(
    text, auto_qualifying_completer, complete_event
):
    pos = text.index('  ') + 1
    cols = [column(c.lower()) for c in cased_users_col_names]
    result = set(auto_qualifying_completer.get_completions(
        Document(text=text, cursor_position=pos),
        complete_event))
    assert set(result) == set(testdata.functions() + cols
        + testdata.builtin_functions() + testdata.keywords())


@pytest.mark.parametrize('text', [
    'SELECT  from users U NATURAL JOIN "Users"',
    'INSERT INTO Orders SELECT  from users U NATURAL JOIN "Users"',
])
def test_suggested_auto_qualified_column_names_two_tables(
    text, auto_qualifying_completer, complete_event
):
    pos = text.index('  ') + 1
    cols = [column('U.' + c.lower()) for c in cased_users_col_names]
    cols += [column('"Users".' + c.lower()) for c in cased_users2_col_names]
    result = set(auto_qualifying_completer.get_completions(
        Document(text=text, cursor_position=pos),
        complete_event))
    assert set(result) == set(testdata.functions() + cols
        + testdata.builtin_functions() + testdata.keywords())


@pytest.mark.parametrize('text', [
    'UPDATE users SET ',
    'INSERT INTO users(',
])
def test_no_column_qualification(
    text, cased_always_qualifying_completer, complete_event
):
    pos = len(text)
    cols = [column(c) for c in cased_users_col_names]
    result = set(cased_always_qualifying_completer.get_completions(
        Document(text=text, cursor_position=pos),
        complete_event))
    assert set(result) == set(cols)


def test_suggested_cased_always_qualified_column_names(
    cased_always_qualifying_completer, complete_event
):
    text = 'SELECT  from users'
    position = len('SELECT ')
    cols = [column('users.' + c) for c in cased_users_col_names]
    result = set(cased_always_qualifying_completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(cased_funcs + cols
        + testdata.builtin_functions() + testdata.keywords())


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
    assert set(result) == set(testdata.columns('users'))

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
    assert set(result) == set(testdata.columns('users'))

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
    assert set(result) == set(testdata.columns('users'))

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
    assert set(result) == set(testdata.columns('users') + testdata.functions() +
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
    assert set(result) == set(testdata.columns('users'))


def test_suggested_cased_column_names_with_alias(cased_completer, complete_event):
    """
    Suggest column names on table alias and dot
    when selecting multiple columns from table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT u.id, u. from users u'
    position = len('SELECT u.id, u.')
    result = set(cased_completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(cased_users_cols)

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
    assert set(result) == set(testdata.columns('users'))


def test_suggest_columns_after_three_way_join(completer, complete_event):
    text = '''SELECT * FROM users u1
              INNER JOIN users u2 ON u1.id = u2.id
              INNER JOIN users u3 ON u2.id = u3.'''
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert (column('id') in
            set(result))

join_condition_texts = [
    'INSERT INTO orders SELECT * FROM users U JOIN "Users" U2 ON ',
    '''INSERT INTO public.orders(orderid)
    SELECT * FROM users U JOIN "Users" U2 ON ''',
    'SELECT * FROM users U JOIN "Users" U2 ON ',
    'SELECT * FROM users U INNER join "Users" U2 ON ',
    'SELECT * FROM USERS U right JOIN "Users" U2 ON ',
    'SELECT * FROM users U LEFT JOIN "Users" U2 ON ',
    'SELECT * FROM Users U FULL JOIN "Users" U2 ON ',
    'SELECT * FROM users U right outer join "Users" U2 ON ',
    'SELECT * FROM Users U LEFT OUTER JOIN "Users" U2 ON ',
    'SELECT * FROM users U FULL OUTER JOIN "Users" U2 ON ',
    '''SELECT *
    FROM users U
    FULL OUTER JOIN "Users" U2 ON
    '''
]

@pytest.mark.parametrize('text', join_condition_texts)
def test_suggested_join_conditions(completer, complete_event, text):
    result = set(completer.get_completions(
        Document(text=text,), complete_event))
    assert set(result) == set([
        alias('U'),
        alias('U2'),
        fk_join('U2.userid = U.id')])

@pytest.mark.parametrize('text', join_condition_texts)
def test_cased_join_conditions(cased_completer, complete_event, text):
    result = set(cased_completer.get_completions(
        Document(text=text), complete_event))
    assert set(result) == set([
        alias('U'),
        alias('U2'),
        fk_join('U2.UserID = U.ID')])

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
        alias('u'),
        alias('u2'),
        alias('users'),
        alias('"Users"')
    ]

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

join_texts = [
    'SELECT * FROM Users JOIN ',
    '''INSERT INTO "Users"
    SELECT *
    FROM Users
    INNER JOIN ''',
    '''INSERT INTO public."Users"(username)
    SELECT *
    FROM Users
    INNER JOIN ''',
    '''SELECT *
    FROM Users
    INNER JOIN '''
]

@pytest.mark.parametrize('text', join_texts)
def test_suggested_joins(completer, complete_event, text):
    result = set(completer.get_completions(
        Document(text=text), complete_event))
    assert set(result) == set(testdata.schemas() + testdata.tables()
        + testdata.views() + [
        join('"Users" ON "Users".userid = Users.id'),
        join('users users2 ON users2.id = Users.parentid'),
        join('users users2 ON users2.parentid = Users.id'),
        ] + testdata.functions())

@pytest.mark.parametrize('text', join_texts)
def test_cased_joins(cased_completer, complete_event, text):
    result = set(cased_completer.get_completions(
        Document(text=text), complete_event))
    assert set(result) == set([schema('PUBLIC')] + cased_rels + [
        join('"Users" ON "Users".UserID = Users.ID'),
        join('Users Users2 ON Users2.ID = Users.PARENTID'),
        join('Users Users2 ON Users2.PARENTID = Users.ID'),
        ])

@pytest.mark.parametrize('text', join_texts)
def test_aliased_joins(aliased_completer, complete_event, text):
    result = set(aliased_completer.get_completions(
        Document(text=text), complete_event))
    assert set(result) == set(testdata.schemas() + aliased_rels + [
        join('"Users" U ON U.userid = Users.id'),
        join('users u ON u.id = Users.parentid'),
        join('users u ON u.parentid = Users.id'),
        ])

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
    assert set(result) == set(testdata.schemas() + testdata.tables()
        + testdata.views() + [
        join('public.users ON users.id = "Users".userid'),
        ] + testdata.functions())

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
    assert set(result) == set(testdata.schemas() + testdata.tables()
        + testdata.views() + testdata.functions())
    assert [c.text for c in result] == [
        'public',
        'orders',
        '"select"',
        'users',
        '"Users"',
        'user_emails',
        '_custom_fun()',
        'custom_fun()',
        'custom_func1()',
        'custom_func2()',
        'set_returning_func()',
        ]

def test_auto_escaped_col_names(completer, complete_event):
    text = 'SELECT  from "select"'
    position = len('SELECT ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(testdata.columns('select') + [
        ] + testdata.functions() +
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
    assert set(result) == set(testdata.schemas() + testdata.datatypes() +
        testdata.tables() + list(testdata.builtin_datatypes()))


def test_suggest_columns_from_escaped_table_alias(completer, complete_event):
    sql = 'select * from "select" s where s.'
    pos = len(sql)
    result = completer.get_completions(Document(text=sql, cursor_position=pos),
                                       complete_event)
    assert set(result) == set(testdata.columns('select'))


def test_suggest_columns_from_set_returning_function(completer, complete_event):
    sql = 'select  from set_returning_func()'
    pos = len('select ')
    result = completer.get_completions(Document(text=sql, cursor_position=pos),
                                       complete_event)
    assert set(result) == set(
        testdata.columns('set_returning_func', typ='functions')
        + testdata.functions()
        + list(testdata.builtin_functions()
        + testdata.keywords()))


def test_suggest_columns_from_aliased_set_returning_function(completer, complete_event):
    sql = 'select f. from set_returning_func() f'
    pos = len('select f.')
    result = completer.get_completions(Document(text=sql, cursor_position=pos),
                                       complete_event)
    assert set(result) == set(testdata.columns('set_returning_func', typ='functions'))


def test_join_functions_using_suggests_common_columns(completer, complete_event):
    text = '''SELECT * FROM set_returning_func() f1
              INNER JOIN set_returning_func() f2 USING ('''
    pos = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set(
        testdata.columns('set_returning_func', typ='functions'))


def test_join_functions_on_suggests_columns_and_join_conditions(completer, complete_event):
    text = '''SELECT * FROM set_returning_func() f1
              INNER JOIN set_returning_func() f2 ON f1.'''
    pos = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set([
         name_join('y = f2.y'),
         name_join('x = f2.x'),
         ] + testdata.columns('set_returning_func', typ='functions'))


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

@pytest.mark.parametrize('sql', [
    'SELECT * FROM users',
    'INSERT INTO users SELECT * FROM users u',
    '''INSERT INTO users(id, parentid, email, first_name, last_name)
    SELECT *
    FROM users u''',
    ])
def test_wildcard_column_expansion(completer, complete_event, sql):
    pos = sql.find('*') + 1

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, parentid, email, first_name, last_name'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions

@pytest.mark.parametrize('sql', [
    'SELECT u.* FROM users u',
    'INSERT INTO public.users SELECT u.* FROM users u',
    '''INSERT INTO users(id, parentid, email, first_name, last_name)
    SELECT u.*
    FROM users u''',
    ])
def test_wildcard_column_expansion_with_alias(completer, complete_event, sql):
    pos = sql.find('*') + 1

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
    assert set(result) == set(testdata.columns('users'))


def test_suggest_columns_from_quoted_table(completer, complete_event):
    text = 'SELECT U. FROM "Users" U'
    pos = len('SELECT U.')
    result = completer.get_completions(Document(text=text, cursor_position=pos),
                                       complete_event)
    assert set(result) == set(testdata.columns('Users'))

@pytest.mark.parametrize('text', ['SELECT * FROM ',
    'SELECT * FROM Orders o CROSS JOIN '])
def test_schema_or_visible_table_completion(completer, complete_event, text):
    result = completer.get_completions(Document(text=text), complete_event)
    assert set(result) == set(testdata.schemas()
        + testdata.views() + testdata.tables() + testdata.functions())

@pytest.mark.parametrize('text', ['SELECT * FROM '])
def test_table_aliases(aliased_completer, complete_event, text):
    result = aliased_completer.get_completions(
        Document(text=text), complete_event)
    assert set(result) == set(testdata.schemas() + aliased_rels)

@pytest.mark.parametrize('text', ['SELECT * FROM Orders o CROSS JOIN '])
def test_duplicate_table_aliases(aliased_completer, complete_event, text):
    result = aliased_completer.get_completions(
        Document(text=text), complete_event)
    assert set(result) == set(testdata.schemas() + [
        table('orders o2'),
        table('users u'),
        table('"Users" U'),
        table('"select" s'),
        view('user_emails ue'),
        function('_custom_fun() cf'),
        function('custom_fun() cf'),
        function('custom_func1() cf'),
        function('custom_func2() cf'),
        function('set_returning_func() srf')])

@pytest.mark.parametrize('text', ['SELECT * FROM Orders o CROSS JOIN '])
def test_duplicate_aliases_with_casing(cased_aliased_completer,
                                        complete_event, text):
    result = cased_aliased_completer.get_completions(
        Document(text=text), complete_event)
    assert set(result) == set([
        schema('PUBLIC'),
        table('Orders O2'),
        table('Users U'),
        table('"Users" U'),
        table('"select" s'),
        view('User_Emails UE'),
        function('_custom_fun() cf'),
        function('Custom_Fun() CF'),
        function('Custom_Func1() CF'),
        function('custom_func2() cf'),
        function('set_returning_func() srf')])

@pytest.mark.parametrize('text', ['SELECT * FROM '])
def test_aliases_with_casing(cased_aliased_completer, complete_event, text):
    result = cased_aliased_completer.get_completions(
        Document(text=text), complete_event)
    assert set(result) == set([schema('PUBLIC')] + cased_aliased_rels)

@pytest.mark.parametrize('text', ['SELECT * FROM '])
def test_table_casing(cased_completer, complete_event, text):
    result = cased_completer.get_completions(
        Document(text=text), complete_event)
    assert set(result) == set([schema('PUBLIC')] + cased_rels)


@pytest.mark.parametrize('text', [
    'INSERT INTO users ()',
    'INSERT INTO users()',
    'INSERT INTO users () SELECT * FROM orders;',
    'INSERT INTO users() SELECT * FROM users u cross join orders o',
])
def test_insert(completer, complete_event, text):
    pos = text.find('(') + 1
    result = completer.get_completions(Document(text=text, cursor_position=pos),
                                       complete_event)
    assert set(result) == set(testdata.columns('users'))


def test_suggest_cte_names(completer, complete_event):
    text = '''
        WITH cte1 AS (SELECT a, b, c FROM foo),
             cte2 AS (SELECT d, e, f FROM bar)
        SELECT * FROM
    '''
    pos = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=pos),
        complete_event)
    expected = set([
        Completion('cte1', 0, display_meta='table'),
        Completion('cte2', 0, display_meta='table'),
    ])
    assert expected <= set(result)


def test_suggest_columns_from_cte(completer, complete_event):
    text = 'WITH cte AS (SELECT foo, bar FROM baz) SELECT  FROM cte'
    pos = len('WITH cte AS (SELECT foo, bar FROM baz) SELECT ')
    result = completer.get_completions(Document(text=text, cursor_position=pos),
                                       complete_event)
    expected = ([Completion('foo', 0, display_meta='column'),
                 Completion('bar', 0, display_meta='column'),
                 ] +
                testdata.functions() +
                testdata.builtin_functions() +
                testdata.keywords()
                )

    assert set(expected) == set(result)


@pytest.mark.parametrize('text', [
    'WITH cte AS (SELECT foo FROM bar) SELECT * FROM cte WHERE cte.',
    'WITH cte AS (SELECT foo FROM bar) SELECT * FROM cte c WHERE c.',
])
def test_cte_qualified_columns(completer, complete_event, text):
    pos = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=pos),
        complete_event)
    expected = [Completion('foo', 0, display_meta='column')]
    assert set(expected) == set(result)


@pytest.mark.parametrize('keyword_casing,expected,texts', [
    ('upper', 'SELECT', ('', 's', 'S', 'Sel')),
    ('lower', 'select', ('', 's', 'S', 'Sel')),
    ('auto', 'SELECT', ('', 'S', 'SEL', 'seL')),
    ('auto', 'select', ('s', 'sel', 'SEl')),
])
def test_keyword_casing_upper(keyword_casing, expected, texts):
    for text in texts:
        completer_ = testdata.get_completer({'keyword_casing': keyword_casing})
        completions = completer_.get_completions(
            Document(text=text, cursor_position=len(text)), complete_event)
        assert expected in [cpl.text for cpl in completions]


def test_keyword_after_alter(completer):
    sql = 'ALTER TABLE users ALTER '
    expected = Completion('COLUMN', start_position=0, display_meta='keyword')
    completions = completer.get_completions(
        Document(text=sql, cursor_position=len(sql)), complete_event)
    assert expected in set(completions)
