from __future__ import unicode_literals
import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
from pgcli.packages.function_metadata import FunctionMetadata

metadata = {
            'tables': {
                'public':   {
                                'users': ['id', 'email', 'first_name', 'last_name'],
                                'orders': ['id', 'ordered_date', 'status'],
                                'select': ['id', 'insert', 'ABC']
                            },
                'custom':   {
                                'users': ['id', 'phone_number'],
                                'Users': ['userid', 'username'],
                                'products': ['id', 'product_name', 'price'],
                                'shipments': ['id', 'address', 'user_id']
                            },
                'Custom':   {
                                'projects': ['projectid', 'name']
                            }},
            'functions': {
                            'public': [
                                ['func1', [], [], [], '', False, False,
                                    False],
                                ['func2', [], [], [], '', False, False,
                                    False]],
                            'custom': [
                                ['func3', [], [], [], '', False, False, False],
                                ['set_returning_func', ['x'], ['integer'], ['o'],
                                    'integer', False, False, True]],
                            'Custom': [
                                ['func4', [], [], [], '', False, False, False]]
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
            # Let all columns be text columns
            columns.extend([(schema, table, col, 'text') for col in cols])

    functions = [FunctionMetadata(schema, *func_meta)
                    for schema, funcs in metadata['functions'].items()
                    for func_meta in funcs]

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
       Completion(text='func1', start_position=0, display_meta='function'),
       Completion(text='func2', start_position=0, display_meta='function'),
       Completion(text='public', start_position=0, display_meta='schema'),
       Completion(text='custom', start_position=0, display_meta='schema'),
       Completion(text='"Custom"', start_position=0, display_meta='schema'),
       Completion(text='users', start_position=0, display_meta='table'),
       Completion(text='"select"', start_position=0, display_meta='table'),
       Completion(text='orders', start_position=0, display_meta='table')])


@pytest.mark.parametrize('text', [
    'SELECT  FROM users',
    'SELECT  FROM "users"',
    ])
def test_suggested_column_names_from_shadowed_visible_table(completer, complete_event, text):
    """
    Suggest column and function names when selecting from table
    :param completer:
    :param complete_event:
    :return:
    """
    position = len('SELECT ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))

    assert set(result) == set([
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
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='product_name', start_position=0, display_meta='column'),
        Completion(text='price', start_position=0, display_meta='column')])


@pytest.mark.parametrize('text', [
    'SELECT * FROM Custom.',
    'SELECT * FROM custom.',
    'SELECT * FROM "custom".',
])
@pytest.mark.parametrize('use_leading_double_quote', [False, True])
def test_suggested_table_names_with_schema_dot(completer, complete_event,
                                               text, use_leading_double_quote):
    if use_leading_double_quote:
        text += '"'
        start_pos = -1
    else:
        start_pos = 0

    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        Completion(text='func3', start_position=start_pos, display_meta='function'),
        Completion(text='users', start_position=start_pos, display_meta='table'),
        Completion(text='"Users"', start_position=start_pos, display_meta='table'),
        Completion(text='products', start_position=start_pos, display_meta='table'),
        Completion(text='shipments', start_position=start_pos, display_meta='table'),
        Completion(text='set_returning_func', start_position=start_pos, display_meta='function'),
    ])

@pytest.mark.parametrize('text', [
    'SELECT * FROM "Custom".',
])
@pytest.mark.parametrize('use_leading_double_quote', [False, True])
def test_suggested_table_names_with_schema_dot2(completer, complete_event,
                                               text, use_leading_double_quote):
    if use_leading_double_quote:
        text += '"'
        start_pos = -1
    else:
        start_pos = 0

    position = len(text)
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set([
        Completion(text='func4', start_position=start_pos, display_meta='function'),
        Completion(text='projects', start_position=start_pos, display_meta='table')
    ])

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
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='product_name', start_position=0, display_meta='column'),
        Completion(text='price', start_position=0, display_meta='column')])

@pytest.mark.parametrize('text', [
    'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON ',
    'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON JOIN public.orders z ON z.id > y.id'
])
def test_suggestions_after_on(completer, complete_event, text):
    position = len('SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        Completion(text='x', start_position=0, display_meta='table alias'),
        Completion(text='y', start_position=0, display_meta='table alias'),
        Completion(text='y.price = x.price', start_position=0, display_meta='name join'),
        Completion(text='y.product_name = x.product_name', start_position=0, display_meta='name join'),
        Completion(text='y.id = x.id', start_position=0, display_meta='name join')])

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
        Completion(text='func1', start_position=0, display_meta='function'),
        Completion(text='func2', start_position=0, display_meta='function'),
        Completion(text='public', start_position=0, display_meta='schema'),
        Completion(text='custom', start_position=0, display_meta='schema'),
        Completion(text='"Custom"', start_position=0, display_meta='schema'),
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
        Completion(text='set_returning_func', start_position=-len('func'), display_meta='function')])


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
        Completion(text='"Users"', display_meta='table'),
        Completion(text='products', display_meta='table'),
        Completion(text='shipments', display_meta='table'),
        ])


def test_suggest_columns_from_aliased_set_returning_function(completer, complete_event):
    sql = 'select f. from custom.set_returning_func() f'
    pos = len('select f.')
    result = completer.get_completions(Document(text=sql, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        Completion(text='x', start_position=0, display_meta='column')])

@pytest.mark.parametrize('text', [
    'SELECT * FROM custom.set_returning_func()',
    'SELECT * FROM Custom.set_returning_func()',
    'SELECT * FROM Custom.Set_Returning_Func()'
])
def test_wildcard_column_expansion_with_function(completer, complete_event, text):
    pos = len('SELECT *')

    completions = completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event)

    col_list = 'x'
    expected = [Completion(text=col_list, start_position=-1,
                          display='*', display_meta='columns')]

    assert expected == completions


def test_wildcard_column_expansion_with_alias_qualifier(completer, complete_event):
    sql = 'SELECT p.* FROM custom.products p'
    pos = len('SELECT p.*')

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, p.product_name, p.price'
    expected = [Completion(text=col_list, start_position=-1,
                          display='*', display_meta='columns')]

    assert expected == completions

@pytest.mark.parametrize('text', [
    'INSERT INTO public.orders(*',
    'INSERT INTO public.Orders(*',
    'INSERT INTO public.orders (*',
    'INSERT INTO public.Orders (*',
    'INSERT INTO orders(*',
    'INSERT INTO Orders(*',
    'INSERT INTO orders (*',
    'INSERT INTO Orders (*',
    'INSERT INTO public.orders(*)',
    'INSERT INTO public.Orders(*)',
    'INSERT INTO public.orders (*)',
    'INSERT INTO public.Orders (*)',
    'INSERT INTO orders(*)',
    'INSERT INTO Orders(*)',
    'INSERT INTO orders (*)',
    'INSERT INTO Orders (*)'
])
def test_wildcard_column_expansion_with_insert(completer, complete_event, text):
    pos = text.index('*') + 1
    completions = completer.get_completions(
        Document(text=text, cursor_position=pos), complete_event)

    expected = [Completion(text='id, ordered_date, status', start_position=-1,
                          display='*', display_meta='columns')]
    assert expected == completions

def test_wildcard_column_expansion_with_table_qualifier(completer, complete_event):
    sql = 'SELECT "select".* FROM public."select"'
    pos = len('SELECT "select".*')

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, "select"."insert", "select"."ABC"'
    expected = [Completion(text=col_list, start_position=-1,
                          display='*', display_meta='columns')]

    assert expected == completions

def test_wildcard_column_expansion_with_two_tables(completer, complete_event):
    sql = 'SELECT * FROM public."select" JOIN custom.users ON true'
    pos = len('SELECT *')

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    cols = ('"select".id, "select"."insert", "select"."ABC", '
        'users.id, users.phone_number')
    expected = [Completion(text=cols, start_position=-1,
        display='*', display_meta='columns')]
    assert completions == expected


def test_wildcard_column_expansion_with_two_tables_and_parent(completer, complete_event):
    sql = 'SELECT "select".* FROM public."select" JOIN custom.users u ON true'
    pos = len('SELECT "select".*')

    completions = completer.get_completions(
        Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, "select"."insert", "select"."ABC"'
    expected = [Completion(text=col_list, start_position=-1,
                          display='*', display_meta='columns')]

    assert expected == completions

@pytest.mark.parametrize('text', [
    'SELECT U. FROM custom.Users U',
    'SELECT U. FROM custom.USERS U',
    'SELECT U. FROM custom.users U',
    'SELECT U. FROM "custom".Users U',
    'SELECT U. FROM "custom".USERS U',
    'SELECT U. FROM "custom".users U'
])
def test_suggest_columns_from_unquoted_table(completer, complete_event, text):
    pos = len('SELECT U.')
    result = completer.get_completions(Document(text=text, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        Completion(text='id', start_position=0, display_meta='column'),
        Completion(text='phone_number', start_position=0, display_meta='column')])

@pytest.mark.parametrize('text', [
    'SELECT U. FROM custom."Users" U',
    'SELECT U. FROM "custom"."Users" U'
])
def test_suggest_columns_from_quoted_table(completer, complete_event, text):
    pos = len('SELECT U.')
    result = completer.get_completions(Document(text=text, cursor_position=pos),
                                       complete_event)
    assert set(result) == set([
        Completion(text='userid', start_position=0, display_meta='column'),
        Completion(text='username', start_position=0, display_meta='column')])
