from __future__ import unicode_literals
import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
from pgcli.pgexecute import FunctionMetadata

metadata = {
            'tables': {
                'public':   {
                                'users': ['id', 'email', 'first_name', 'last_name'],
                                'orders': ['id', 'ordered_date', 'status'],
                                'select': ['id', 'insert', 'ABC']
                            },
                'custom':   {
                                'users': ['id', 'phone_number'],
                                'products': ['id', 'product_name', 'price'],
                                'shipments': ['id', 'address', 'user_id']
                            }},
            'functions': {
                            'public':   ['func1', 'func2'],
                            'custom':   ['func3', 'func4'],
                         },
            'datatypes': {
                            'public':   ['typ1', 'typ2'],
                            'custom':   ['typ3', 'typ4'],
                         },
            }

@pytest.fixture
def completer():

    import pgcli.pgcompleter as pgcompleter
    comp = pgcompleter.PGCompleter(smart_completion=True)

    schemata, tables, columns = [], [], []

    for schema, tbls in metadata['tables'].items():
        schemata.append(schema)

        for table, cols in tbls.items():
            tables.append((schema, table))
            columns.extend([(schema, table, col) for col in cols])

    functions = [FunctionMetadata(schema, func, '', '', False, False, False)
                    for schema, funcs in metadata['functions'].items()
                    for func in funcs]

    datatypes = [(schema, datatype)
                    for schema, datatypes in metadata['datatypes'].items()
                    for datatype in datatypes]

    comp.extend_schemata(schemata)
    comp.extend_relations(tables, kind='tables')
    comp.extend_columns(columns, kind='tables')
    comp.extend_functions(functions)
    comp.extend_datatypes(datatypes)
    comp.set_search_path(['public'])

    return comp

@pytest.fixture
def complete_event():
    from mock import Mock
    return Mock()

def test_schema_or_visible_table_completion(completer, complete_event):
    text = 'SELECT * FROM '
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
       Completion(text='public', start_position=0, display_meta='schema'),
       Completion(text='custom', start_position=0, display_meta='schema'),
       Completion(text='users', start_position=0, display_meta='table'),
       Completion(text='"select"', start_position=0, display_meta='table'),
       Completion(text='orders', start_position=0, display_meta='table')])

def test_suggested_column_names_from_shadowed_visible_table(completer, complete_event):
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
        Completion(text='func1', start_position=0, display_meta='function'),
        Completion(text='func2', start_position=0, display_meta='function')] +
        list(map(lambda f: Completion(f, display_meta='function'), completer.functions)) +
        list(map(lambda x: Completion(x, display_meta='keyword'), completer.keywords))
        )

def test_suggested_column_names_from_qualified_shadowed_table(completer, complete_event):
    text = 'SELECT  from custom.users'
    position = len('SELECT ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='phone_number', start_position=0, display_meta='column'),
        Completion(text='func1', start_position=0, display_meta='function'),
        Completion(text='func2', start_position=0, display_meta='function')] +
        list(map(lambda f: Completion(f, display_meta='function'), completer.functions)) +
        list(map(lambda x: Completion(x, display_meta='keyword'), completer.keywords))
        )

def test_suggested_column_names_from_schema_qualifed_table(completer, complete_event):
    """
    Suggest column and function names when selecting from a qualified-table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT  from custom.products'
    position = len('SELECT ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position), complete_event))
    assert set(result) == set([
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='product_name', start_position=0, display_meta='column'),
        Completion(text='price', start_position=0, display_meta='column'),
        Completion(text='func1', start_position=0, display_meta='function'),
        Completion(text='func2', start_position=0, display_meta='function')] +
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
    text = 'SELECT MAX( from custom.products'
    position = len('SELECT MAX(')
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert set(result) == set([
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='product_name', start_position=0, display_meta='column'),
        Completion(text='price', start_position=0, display_meta='column')])

def test_suggested_table_names_with_schema_dot(completer, complete_event):
    text = 'SELECT * FROM custom.'
    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        Completion(text='users', start_position=0, display_meta='table'),
        Completion(text='products', start_position=0, display_meta='table'),
        Completion(text='shipments', start_position=0, display_meta='table')])

def test_suggested_column_names_with_qualified_alias(completer, complete_event):
    """
    Suggest column names on table alias and dot
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT p. from custom.products p'
    position = len('SELECT p.')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='product_name', start_position=0, display_meta='column'),
        Completion(text='price', start_position=0, display_meta='column')])

def test_suggested_multiple_column_names(completer, complete_event):
    """
    Suggest column and function names when selecting multiple
    columns from table
    :param completer:
    :param complete_event:
    :return:
    """
    text = 'SELECT id,  from custom.products'
    position = len('SELECT id, ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='product_name', start_position=0, display_meta='column'),
        Completion(text='price', start_position=0, display_meta='column'),
        Completion(text='func1', start_position=0, display_meta='function'),
        Completion(text='func2', start_position=0, display_meta='function')] +
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
    text = 'SELECT p.id, p. from custom.products p'
    position = len('SELECT u.id, u.')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='*', start_position=0, display_meta='column'),
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='product_name', start_position=0, display_meta='column'),
        Completion(text='price', start_position=0, display_meta='column')])

def test_suggested_aliases_after_on(completer, complete_event):
    text = 'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON '
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='x', start_position=0, display_meta='table alias'),
        Completion(text='y', start_position=0, display_meta='table alias')])

def test_suggested_aliases_after_on_right_side(completer, complete_event):
    text = 'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON x.id = '
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='x', start_position=0, display_meta='table alias'),
        Completion(text='y', start_position=0, display_meta='table alias')])

def test_table_names_after_from(completer, complete_event):
    text = 'SELECT * FROM '
    position = len('SELECT * FROM ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='public', start_position=0, display_meta='schema'),
        Completion(text='custom', start_position=0, display_meta='schema'),
        Completion(text='users', start_position=0, display_meta='table'),
        Completion(text='orders', start_position=0, display_meta='table'),
        Completion(text='"select"', start_position=0, display_meta='table'),
        ])

def test_schema_qualified_function_name(completer, complete_event):
    text = 'SELECT custom.func'
    postion = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=postion), complete_event))
    assert result == set([
        Completion(text='func3', start_position=-len('func'), display_meta='function'),
        Completion(text='func4', start_position=-len('func'), display_meta='function')])


@pytest.mark.parametrize('text', [
    'SELECT 1::custom.',
    'CREATE TABLE foo (bar custom.',
    'CREATE FUNCTION foo (bar INT, baz custom.',
    'ALTER TABLE foo ALTER COLUMN bar TYPE custom.',
])
def test_schema_qualified_type_name(text, completer, complete_event):
    pos = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event)
    assert set(result) == set([
        Completion(text='typ3', display_meta='datatype'),
        Completion(text='typ4', display_meta='datatype'),
        Completion(text='users', display_meta='table'),
        Completion(text='products', display_meta='table'),
        Completion(text='shipments', display_meta='table'),
        ])
