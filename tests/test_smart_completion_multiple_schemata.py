from __future__ import unicode_literals
import pytest
import itertools
from metadata import (MetaData, alias, name_join, fk_join, join,
    schema, table, function, wildcard_expansion, column)
from prompt_toolkit.document import Document

metadata = {
    'tables': {
        'public': {
            'users': ['id', 'email', 'first_name', 'last_name'],
            'orders': ['id', 'ordered_date', 'status'],
            'select': ['id', 'insert', 'ABC']
        },
        'custom': {
            'users': ['id', 'phone_number'],
            'Users': ['userid', 'username'],
            'products': ['id', 'product_name', 'price'],
            'shipments': ['id', 'address', 'user_id']
        },
        'Custom': {
            'projects': ['projectid', 'name']
        },
        'blog': {
            'entries': ['entryid', 'entrytitle', 'entrytext'],
            'tags': ['tagid', 'name'],
            'entrytags': ['entryid', 'tagid'],
            'entacclog': ['entryid', 'username', 'datestamp'],
        }
    },
    'functions': {
        'public': [
            ['func1', [], [], [], '', False, False, False],
            ['func2', [], [], [], '', False, False, False]],
        'custom': [
            ['func3', [], [], [], '', False, False, False],
            ['set_returning_func', ['x'], ['integer'], ['o'],
                'integer', False, False, True]],
        'Custom': [
            ['func4', [], [], [], '', False, False, False]],
        'blog': [
            ['extract_entry_symbols', ['_entryid', 'symbol'],
                ['integer', 'text'], ['i', 'o'], '', False, False, True],
            ['enter_entry', ['_title', '_text', 'entryid'],
                ['text', 'text', 'integer'], ['i', 'i', 'o'],
                '', False, False, False]],
     },
    'datatypes': {
        'public': ['typ1', 'typ2'],
        'custom': ['typ3', 'typ4'],
     },
    'foreignkeys': {
        'custom': [
            ('public', 'users', 'id', 'custom', 'shipments', 'user_id')
        ],
        'blog': [
            ('blog', 'entries', 'entryid', 'blog', 'entacclog', 'entryid'),
            ('blog', 'entries', 'entryid', 'blog', 'entrytags', 'entryid'),
            ('blog', 'tags', 'tagid', 'blog', 'entrytags', 'tagid'),
        ],
    },
}

testdata = MetaData(metadata)
cased_schemas = [schema(x) for x in ('public', 'blog', 'CUSTOM', '"Custom"')]

casing = ('SELECT', 'Orders', 'User_Emails', 'CUSTOM', 'Func1', 'Entries',
          'Tags', 'EntryTags', 'EntAccLog',
          'EntryID', 'EntryTitle', 'EntryText')

completers = testdata.get_completers(casing)
parametrize = pytest.mark.parametrize


@pytest.fixture
def complete_event():
    from mock import Mock
    return Mock()


@parametrize(
    'completer', completers(
        filtr=True, casing=False, qualify=['never', 'if_more_than_one_table']
    )
)
@parametrize('table', [
    'users',
    '"users"',
    ])
def test_suggested_column_names_from_shadowed_visible_table(
    completer, complete_event, table
):
    text = 'SELECT  FROM ' + table
    position = len('SELECT ')
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))

    assert set(result) == set(testdata.columns('users') +
        testdata.functions() +
        list(testdata.builtin_functions() +
        testdata.keywords())
        )


@parametrize(
    'completer', completers(
        filtr=True, casing=False, qualify=['never', 'if_more_than_one_table']
    )
)
@parametrize('text', [
    'SELECT  from custom.users',
    'WITH users as (SELECT 1 AS foo) SELECT  from custom.users',
    ])
def test_suggested_column_names_from_qualified_shadowed_table(
    completer, complete_event, text
):
    position = text.find('  ') + 1
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(testdata.columns('users', 'custom') +
        testdata.functions() +
        list(testdata.builtin_functions() +
        testdata.keywords())
        )


@parametrize(
    'completer', completers(
        filtr=True, casing=False, qualify=['never', 'if_more_than_one_table']
    )
)
@parametrize('text', [
    'WITH users as (SELECT 1 AS foo) SELECT  from users',
    ])
def test_suggested_column_names_from_cte(
    completer, complete_event, text
):
    position = text.find('  ') + 1
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([column('foo')] + testdata.functions() +
        list(testdata.builtin_functions() + testdata.keywords())
    )


@parametrize('completer', completers(casing=False))
@parametrize('text', [
    'SELECT * FROM users JOIN custom.shipments ON ',
    '''SELECT *
    FROM public.users
    JOIN custom.shipments ON '''
])
def test_suggested_join_conditions(completer, complete_event, text):
    position = len(text)
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        alias('users'),
        alias('shipments'),
        name_join('shipments.id = users.id'),
        fk_join('shipments.user_id = users.id')])


@parametrize('completer', completers(filtr=True, casing=False, alias=False))
@parametrize(('query', 'tbl'), itertools.product((
    'SELECT * FROM public.{0} RIGHT OUTER JOIN ',
    '''SELECT *
    FROM {0}
    JOIN '''
), ('users', '"users"', 'Users')))
def test_suggested_joins(completer, complete_event, query, tbl):
    text = query.format(tbl)
    position = len(text)
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(testdata.schemas() + testdata.tables() + [
        join('custom.shipments ON shipments.user_id = {0}.id'.format(tbl)),
        ] + testdata.functions())


@parametrize(
    'completer', completers(
        filtr=True, casing=False, qualify=['never', 'if_more_than_one_table']
    )
)
def test_suggested_column_names_from_schema_qualifed_table(
    completer, complete_event
):
    text = 'SELECT  from custom.products'
    position = len('SELECT ')
    result = set(
        completer.get_completions(
            Document(text=text, cursor_position=position), complete_event
        )
    )
    assert set(result) == set(
        testdata.columns('products', 'custom') + testdata.functions() +
        list(testdata.builtin_functions() + testdata.keywords())
    )


@parametrize(
    'completer', completers(
        filtr=True, casing=False, qualify=['never', 'if_more_than_one_table']
    )
)
def test_suggested_column_names_in_function(
    completer, complete_event
):
    text = 'SELECT MAX( from custom.products'
    position = len('SELECT MAX(')
    result = completer.get_completions(
        Document(text=text, cursor_position=position), complete_event
    )
    assert set(result) == set(testdata.columns('products', 'custom'))


@parametrize('completer', completers(casing=False, alias=False))
@parametrize('text', [
    'SELECT * FROM Custom.',
    'SELECT * FROM custom.',
    'SELECT * FROM "custom".',
])
@parametrize('use_leading_double_quote', [False, True])
def test_suggested_table_names_with_schema_dot(
    completer, complete_event, text, use_leading_double_quote
):
    if use_leading_double_quote:
        text += '"'
        start_pos = -1
    else:
        start_pos = 0

    position = len(text)
    result = completer.get_completions(Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set(testdata.tables('custom', start_pos)
        + testdata.functions('custom', start_pos))


@parametrize('completer', completers(casing=False, alias=False))
@parametrize('text', [
    'SELECT * FROM "Custom".',
])
@parametrize('use_leading_double_quote', [False, True])
def test_suggested_table_names_with_schema_dot2(
    completer, complete_event, text, use_leading_double_quote
):
    if use_leading_double_quote:
        text += '"'
        start_pos = -1
    else:
        start_pos = 0

    position = len(text)
    result = completer.get_completions(Document(text=text, cursor_position=position), complete_event)
    assert set(result) == set(testdata.functions('Custom', start_pos) +
        testdata.tables('Custom', start_pos))


@parametrize('completer', completers(filtr=True, casing=False))
def test_suggested_column_names_with_qualified_alias(completer, complete_event):
    text = 'SELECT p. from custom.products p'
    position = len('SELECT p.')
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(testdata.columns('products', 'custom'))


@parametrize(
    'completer', completers(
        filtr=True, casing=False, qualify=['never', 'if_more_than_one_table']
    )
)
def test_suggested_multiple_column_names(completer, complete_event):
    text = 'SELECT id,  from custom.products'
    position = len('SELECT id, ')
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(testdata.columns('products', 'custom') +
        testdata.functions() +
        list(testdata.builtin_functions() +
        testdata.keywords())
        )


@parametrize('completer', completers(filtr=True, casing=False))
def test_suggested_multiple_column_names_with_alias(completer, complete_event):
    text = 'SELECT p.id, p. from custom.products p'
    position = len('SELECT u.id, u.')
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(testdata.columns('products', 'custom'))


@parametrize('completer', completers(filtr=True, casing=False))
@parametrize('text', [
    'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON ',
    'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON JOIN public.orders z ON z.id > y.id'
])
def test_suggestions_after_on(completer, complete_event, text):
    position = len('SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON ')
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        alias('x'),
        alias('y'),
        name_join('y.price = x.price'),
        name_join('y.product_name = x.product_name'),
        name_join('y.id = x.id')])


@parametrize('completer', completers())
def test_suggested_aliases_after_on_right_side(completer, complete_event):
    text = 'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON x.id = '
    position = len(text)
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set([
        alias('x'),
        alias('y')])


@parametrize('completer', completers(filtr=True, casing=False, alias=False))
def test_table_names_after_from(completer, complete_event):
    text = ('SELECT * FROM ')
    position = len(text)
    result = set(completer.get_completions(Document(text=text, cursor_position=position),
        complete_event))
    assert set(result) == set(testdata.schemas() + testdata.tables()
        + testdata.functions())


@parametrize('completer', completers(filtr=True, casing=False))
def test_schema_qualified_function_name(completer, complete_event):
    text = 'SELECT custom.func'
    postion = len(text)
    result = set(completer.get_completions(Document(text=text, cursor_position=postion), complete_event))
    assert result == set([
        function('func3()', -len('func')),
        function('set_returning_func()', -len('func'))])


@parametrize('completer', completers(filtr=True, casing=False))
@parametrize('text', [
    'SELECT 1::custom.',
    'CREATE TABLE foo (bar custom.',
    'CREATE FUNCTION foo (bar INT, baz custom.',
    'ALTER TABLE foo ALTER COLUMN bar TYPE custom.',
])
def test_schema_qualified_type_name(completer, text, complete_event):
    pos = len(text)
    result = completer.get_completions(Document(text=text, cursor_position=pos), complete_event)
    assert set(result) == set(testdata.datatypes('custom')
        + testdata.tables('custom'))


@parametrize('completer', completers(filtr=True, casing=False))
def test_suggest_columns_from_aliased_set_returning_function(
    completer, complete_event
):
    sql = 'select f. from custom.set_returning_func() f'
    pos = len('select f.')
    result = completer.get_completions(Document(text=sql, cursor_position=pos), complete_event
    )
    assert set(result) == set(
        testdata.columns('set_returning_func', 'custom', 'functions'))


@parametrize(
    'completer',
    completers(
        filtr=True, casing=False, qualify=['never', 'if_more_than_one_table']
    )
)
@parametrize('text', [
    'SELECT * FROM custom.set_returning_func()',
    'SELECT * FROM Custom.set_returning_func()',
    'SELECT * FROM Custom.Set_Returning_Func()'
])
def test_wildcard_column_expansion_with_function(
    completer, complete_event, text
):
    pos = len('SELECT *')

    completions = completer.get_completions(Document(text=text, cursor_position=pos), complete_event)

    col_list = 'x'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize('completer', completers(filtr=True, casing=False))
def test_wildcard_column_expansion_with_alias_qualifier(
    completer, complete_event
):
    sql = 'SELECT p.* FROM custom.products p'
    pos = len('SELECT p.*')

    completions = completer.get_completions(Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, p.product_name, p.price'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize('completer', completers(filtr=True, casing=False))
@parametrize('text', [
    '''
    SELECT count(1) FROM users;
    CREATE FUNCTION foo(custom.products _products) returns custom.shipments
    LANGUAGE SQL
    AS $foo$
    SELECT 1 FROM custom.shipments;
    INSERT INTO public.orders(*) values(-1, now(), 'preliminary');
    SELECT 2 FROM custom.users;
    $foo$;
    SELECT count(1) FROM custom.shipments;
    ''',
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
def test_wildcard_column_expansion_with_insert(
    completer, complete_event, text
):
    pos = text.index('*') + 1
    completions = completer.get_completions(Document(text=text, cursor_position=pos), complete_event)

    expected = [wildcard_expansion('id, ordered_date, status')]
    assert expected == completions


@parametrize('completer', completers(filtr=True, casing=False))
def test_wildcard_column_expansion_with_table_qualifier(
    completer, complete_event
):
    sql = 'SELECT "select".* FROM public."select"'
    pos = len('SELECT "select".*')

    completions = completer.get_completions(Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, "select"."insert", "select"."ABC"'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize(
    'completer',
    completers(
        filtr=True, casing=False, qualify=['if_more_than_one_table', 'always']
    )
)
def test_wildcard_column_expansion_with_two_tables(
    completer, complete_event
):
    sql = 'SELECT * FROM public."select" JOIN custom.users ON true'
    pos = len('SELECT *')

    completions = completer.get_completions(Document(text=sql, cursor_position=pos), complete_event)

    cols = ('"select".id, "select"."insert", "select"."ABC", '
        'users.id, users.phone_number')
    expected = [wildcard_expansion(cols)]
    assert completions == expected


@parametrize('completer', completers(filtr=True, casing=False))
def test_wildcard_column_expansion_with_two_tables_and_parent(
    completer, complete_event
):
    sql = 'SELECT "select".* FROM public."select" JOIN custom.users u ON true'
    pos = len('SELECT "select".*')

    completions = completer.get_completions(Document(text=sql, cursor_position=pos), complete_event)

    col_list = 'id, "select"."insert", "select"."ABC"'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize('completer', completers(filtr=True, casing=False))
@parametrize('text', [
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
    assert set(result) == set(testdata.columns('users', 'custom'))


@parametrize('completer', completers(filtr=True, casing=False))
@parametrize('text', [
    'SELECT U. FROM custom."Users" U',
    'SELECT U. FROM "custom"."Users" U'
])
def test_suggest_columns_from_quoted_table(completer, complete_event, text):
    pos = len('SELECT U.')
    result = completer.get_completions(Document(text=text, cursor_position=pos), complete_event
    )
    assert set(result) == set(testdata.columns('Users', 'custom'))

texts = ['SELECT * FROM ', 'SELECT * FROM public.Orders O CROSS JOIN ']


@parametrize('completer', completers(filtr=True, casing=False, alias=False))
@parametrize('text', texts)
def test_schema_or_visible_table_completion(completer, complete_event, text):
    result = completer.get_completions(Document(text=text), complete_event)
    assert set(result) == set(testdata.schemas()
        + testdata.views() + testdata.tables() + testdata.functions())


@parametrize('completer', completers(alias=True, casing=False, filtr=True))
@parametrize('text', texts)
def test_table_aliases(completer, complete_event, text):
    result = completer.get_completions(Document(text=text), complete_event)
    assert set(result) == set(testdata.schemas() + [
        table('users u'),
        table('orders o' if text == 'SELECT * FROM ' else 'orders o2'),
        table('"select" s'),
        function('func1() f'),
        function('func2() f')])


@parametrize('completer', completers(alias=True, casing=True, filtr=True))
@parametrize('text', texts)
def test_aliases_with_casing(completer, complete_event, text):
    result = completer.get_completions(Document(text=text), complete_event)
    assert set(result) == set(cased_schemas + [
        table('users u'),
        table('Orders O' if text == 'SELECT * FROM ' else 'Orders O2'),
        table('"select" s'),
        function('Func1() F'),
        function('func2() f')])


@parametrize('completer', completers(alias=False, casing=True, filtr=True))
@parametrize('text', texts)
def test_table_casing(completer, complete_event, text):
    result = completer.get_completions(Document(text=text), complete_event)
    assert set(result) == set(cased_schemas + [
        table('users'),
        table('Orders'),
        table('"select"'),
        function('Func1()'),
        function('func2()')])


@parametrize('completer', completers(alias=False, casing=True))
def test_alias_search_without_aliases2(completer, complete_event
):
    text = 'SELECT * FROM blog.et'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[0] == table('EntryTags', -2)


@parametrize('completer', completers(alias=False, casing=True))
def test_alias_search_without_aliases1(completer, complete_event
):
    text = 'SELECT * FROM blog.e'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[0] == table('Entries', -1)


@parametrize('completer', completers(alias=True, casing=True))
def test_alias_search_with_aliases2(completer, complete_event):
    text = 'SELECT * FROM blog.et'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[0] == table('EntryTags ET', -2)


@parametrize('completer', completers(alias=True, casing=True))
def test_alias_search_with_aliases1(completer, complete_event):
    text = 'SELECT * FROM blog.e'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[0] == table('Entries E', -1)


@parametrize('completer', completers(alias=True, casing=True))
def test_join_alias_search_with_aliases1(completer,
                                         complete_event):
    text = 'SELECT * FROM blog.Entries E JOIN blog.e'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[:2] == [table('Entries E2', -1), join(
        'EntAccLog EAL ON EAL.EntryID = E.EntryID', -1)]


@parametrize('completer', completers(alias=False, casing=True))
def test_join_alias_search_without_aliases1(completer, complete_event):
    text = 'SELECT * FROM blog.Entries JOIN blog.e'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[:2] == [table('Entries', -1), join(
        'EntAccLog ON EntAccLog.EntryID = Entries.EntryID', -1)]


@parametrize('completer', completers(alias=True, casing=True))
def test_join_alias_search_with_aliases2(completer, complete_event):
    text = 'SELECT * FROM blog.Entries E JOIN blog.et'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[0] == join('EntryTags ET ON ET.EntryID = E.EntryID', -2)


@parametrize('completer', completers(alias=False, casing=True))
def test_join_alias_search_without_aliases2(completer, complete_event):
    text = 'SELECT * FROM blog.Entries JOIN blog.et'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[0] == join(
        'EntryTags ON EntryTags.EntryID = Entries.EntryID', -2)


@parametrize('completer', completers())
def test_function_alias_search_without_aliases(completer, complete_event):
    text = 'SELECT blog.ees'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[0] == function('extract_entry_symbols()', -3)


@parametrize('completer', completers())
def test_function_alias_search_with_aliases(completer, complete_event):
    text = 'SELECT blog.ee'
    result = completer.get_completions(Document(text=text), complete_event)
    assert result[0] == function('enter_entry()', -2)


@parametrize(
    'completer',
    completers(
        filtr=True, casing=True, qualify=['if_more_than_one_table', 'never']
    )
)
def test_column_alias_search(completer, complete_event):
    text = 'SELECT et FROM blog.Entries E'
    result = completer.get_completions(
        Document(text, cursor_position=len('SELECT et')), complete_event
    )
    cols = ('EntryText', 'EntryTitle', 'EntryID')
    assert result[:3] == [column(c, -2) for c in cols]


@parametrize('completer', completers(casing=True))
def test_column_alias_search_qualified(completer, complete_event):
    text = 'SELECT E.ei FROM blog.Entries E'
    result = completer.get_completions(Document(text, cursor_position=len('SELECT E.ei')), complete_event)
    cols = ('EntryID', 'EntryTitle')
    assert result[:3] == [column(c, -2) for c in cols]


@parametrize('completer', completers(casing=False, filtr=False, alias=False))
def test_schema_object_order(completer, complete_event):
    text = 'SELECT * FROM u'
    position = len('SELECT * FROM u')
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event
    )
    assert result[:3] == [
        table(t, pos=-1) for t in ('users', 'custom."Users"', 'custom.users')
    ]

@parametrize('completer', completers(casing=False, filtr=False, alias=False))
def test_all_schema_objects(completer, complete_event):
    text = ('SELECT * FROM ')
    position = len(text)
    result = set(
        completer.get_completions(
            Document(text=text, cursor_position=position),
            complete_event
        )
    )
    assert result >= set(
        [table(x) for x in ('orders', '"select"', 'custom.shipments')]
        + [function(x+'()') for x in ('func2', 'custom.func3')]
    )


@parametrize('completer', completers(filtr=False, alias=False, casing=True))
def test_all_schema_objects_with_casing(completer, complete_event):
    text = ('SELECT * FROM ')
    position = len(text)
    result = set(
        completer.get_completions(
            Document(text=text, cursor_position=position),
            complete_event
        )
    )
    assert result >= set(
        [table(x) for x in ('Orders', '"select"', 'CUSTOM.shipments')]
        + [function(x+'()') for x in ('func2', 'CUSTOM.func3')]
    )


@parametrize('completer', completers(casing=False, filtr=False, alias=True))
def test_all_schema_objects_with_aliases(completer, complete_event):
    text = ('SELECT * FROM ')
    position = len(text)
    result = set(
        completer.get_completions(
            Document(text=text, cursor_position=position),
            complete_event
        )
    )
    assert result >= set(
        [table(x) for x in ('orders o', '"select" s', 'custom.shipments s')]
        + [function(x) for x in ('func2() f', 'custom.func3() f')]
    )
