from __future__ import unicode_literals
import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
from pgcli.pgexecute import FunctionMetadata

metadata = {
                'tables': {
                    'users': ['id', 'email', 'first_name', 'last_name'],
                    'orders': ['id', 'ordered_date', 'status', 'email'],
                    'select': ['id', 'insert', 'ABC']},
                'views': {
                    'user_emails': ['id', 'email']},
                'functions': ['custom_func1', 'custom_func2'],
                'datatypes': ['custom_type1', 'custom_type2'],
            }

@pytest.fixture
def completer():

    import pgcli.pgcompleter as pgcompleter
    comp = pgcompleter.PGCompleter(smart_completion=True)

    schemata = ['public']
    comp.extend_schemata(schemata)

    # tables
    tables, columns = [], []
    for table, cols in metadata['tables'].items():
        tables.append(('public', table))
        columns.extend([('public', table, col) for col in cols])

    comp.extend_relations(tables, kind='tables')
    comp.extend_columns(columns, kind='tables')

    # views
    views, columns = [], []
    for view, cols in metadata['views'].items():
        views.append(('public', view))
        columns.extend([('public', view, col) for col in cols])

    comp.extend_relations(views, kind='views')
    comp.extend_columns(columns, kind='views')

    # functions
    functions = [FunctionMetadata('public', func, '', '', False, False, False)
                 for func in metadata['functions']]
    comp.extend_functions(functions)

    # types
    datatypes = [('public', typ) for typ in metadata['datatypes']]
    comp.extend_datatypes(datatypes)

    comp.set_search_path(['public'])

    return comp

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
    assert set(map(lambda x: Completion(x, display_meta='keyword'),
                    completer.keywords)) == result

def test_select_keyword_completion(completer, complete_event):
    text = 'SEL'
    position = len('SEL')
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert set(result) == set([Completion(text='SELECT', start_position=-3,
                                          display_meta='keyword')])


def test_schema_or_visible_table_completion(completer, complete_event):
    text = 'SELECT * FROM '
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        Completion(text='public', start_position=0, display_meta='schema'),
        Completion(text='users', start_position=0, display_meta='table'),
        Completion(text='"select"', start_position=0, display_meta='table'),
        Completion(text='orders', start_position=0, display_meta='table'),
        Completion(text='user_emails', start_position=0, display_meta='view')])


def test_builtin_function_name_completion(completer, complete_event):
    text = 'SELECT MA'
    position = len('SELECT MA')
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([Completion(text='MAX', start_position=-2, display_meta='function'),
                               Completion(text='MAXEXTENTS', start_position=-2, display_meta='keyword'),
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
        Completion(text='custom_func1', start_position=-2, display_meta='function'),
        Completion(text='custom_func2', start_position=-2, display_meta='function'),
        Completion(text='CURRENT', start_position=-2, display_meta='keyword'),
        ])


def test_user_function_name_completion_matches_anywhere(completer,
                                                        complete_event):
    text = 'SELECT om'
    position = len('SELECT om')
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        Completion(text='custom_func1', start_position=-2, display_meta='function'),
        Completion(text='custom_func2', start_position=-2, display_meta='function')])


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
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        Completion(text='first_name', start_position=0, display_meta='column'),
        Completion(text='last_name', start_position=0, display_meta='column'),
        Completion(text='custom_func1', start_position=0, display_meta='function'),
        Completion(text='custom_func2', start_position=0, display_meta='function')] +
        list(map(lambda f: Completion(f, display_meta='function'), completer.functions)) +
        list(map(lambda x: Completion(x, display_meta='keyword'), completer.keywords))
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
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        Completion(text='first_name', start_position=0, display_meta='column'),
        Completion(text='last_name', start_position=0, display_meta='column')])

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
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        Completion(text='first_name', start_position=0, display_meta='column'),
        Completion(text='last_name', start_position=0, display_meta='column')])

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
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        Completion(text='first_name', start_position=0, display_meta='column'),
        Completion(text='last_name', start_position=0, display_meta='column')])

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
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        Completion(text='first_name', start_position=0, display_meta='column'),
        Completion(text='last_name', start_position=0, display_meta='column'),
        Completion(text='custom_func1', start_position=0, display_meta='function'),
        Completion(text='custom_func2', start_position=0, display_meta='function')] +
        list(map(lambda f: Completion(f, display_meta='function'), completer.functions)) +
        list(map(lambda x: Completion(x, display_meta='keyword'), completer.keywords))
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
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        Completion(text='first_name', start_position=0, display_meta='column'),
        Completion(text='last_name', start_position=0, display_meta='column')])

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
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        Completion(text='first_name', start_position=0, display_meta='column'),
        Completion(text='last_name', start_position=0, display_meta='column')])

def test_suggested_aliases_after_on(completer, complete_event):
    text = 'SELECT u.name, o.id FROM users u JOIN orders o ON '
    position = len('SELECT u.name, o.id FROM users u JOIN orders o ON ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='u', start_position=0, display_meta='table alias'),
        Completion(text='o', start_position=0, display_meta='table alias')])

def test_suggested_aliases_after_on_right_side(completer, complete_event):
    text = 'SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = '
    position = len('SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='u', start_position=0, display_meta='table alias'),
        Completion(text='o', start_position=0, display_meta='table alias')])

def test_suggested_tables_after_on(completer, complete_event):
    text = 'SELECT users.name, orders.id FROM users JOIN orders ON '
    position = len('SELECT users.name, orders.id FROM users JOIN orders ON ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='users', start_position=0, display_meta='table alias'),
        Completion(text='orders', start_position=0, display_meta='table alias')])

def test_suggested_tables_after_on_right_side(completer, complete_event):
    text = 'SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = '
    position = len('SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='users', start_position=0, display_meta='table alias'),
        Completion(text='orders', start_position=0, display_meta='table alias')])

def test_join_using_suggests_common_columns(completer, complete_event):
    text = 'SELECT * FROM users INNER JOIN orders USING ('
    pos = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set([
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        ])

def test_join_using_suggests_columns_after_first_column(completer, complete_event):
    text = 'SELECT * FROM users INNER JOIN orders USING (id,'
    pos = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event))
    assert set(result) == set([
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='email', start_position=0, display_meta='column'),
        ])

def test_table_names_after_from(completer, complete_event):
    text = 'SELECT * FROM '
    position = len('SELECT * FROM ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='public', start_position=0, display_meta='schema'),
        Completion(text='users', start_position=0, display_meta='table'),
        Completion(text='orders', start_position=0, display_meta='table'),
        Completion(text='"select"', start_position=0, display_meta='table'),
        Completion(text='user_emails', start_position=0, display_meta='view'),
        ])

def test_auto_escaped_col_names(completer, complete_event):
    text = 'SELECT  from "select"'
    position = len('SELECT ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='"insert"', start_position=0, display_meta='column'),
        Completion(text='"ABC"', start_position=0, display_meta='column'),
        Completion(text='custom_func1', start_position=0, display_meta='function'),
        Completion(text='custom_func2', start_position=0, display_meta='function')] +
        list(map(lambda f: Completion(f, display_meta='function'), completer.functions)) +
        list(map(lambda x: Completion(x, display_meta='keyword'), completer.keywords))
        )


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
        Completion(text='custom_type1', start_position=0, display_meta='datatype'),
        Completion(text='custom_type2', start_position=0, display_meta='datatype'),
        Completion(text='public', start_position=0, display_meta='schema'),
        Completion(text='users', start_position=0, display_meta='table'),
        Completion(text='orders', start_position=0, display_meta='table'),
        Completion(text='"select"', start_position=0, display_meta='table')] +
        list(map(lambda f: Completion(f, display_meta='datatype'), completer.datatypes)))


def test_suggest_columns_from_escaped_table_alias(completer, complete_event):
    sql = 'select * from "select" s where s.'
    pos = len(sql)
    result = completer.get_completions(Document(text=sql, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='"insert"', start_position=0, display_meta='column'),
        Completion(text='"ABC"', start_position=0, display_meta='column'),
    ])
