from __future__ import unicode_literals, print_function

import itertools
from metadata import (MetaData, alias, name_join, fk_join, join,
    schema, table, function, wildcard_expansion, column,
    get_result, result_set, qual, no_qual, parametrize)

metadata = {
    'tables': {
        'public': {
            'users': ['id', 'email', 'first_name', 'last_name'],
            'orders': ['id', 'ordered_date', 'status', 'datestamp'],
            'select': ['id', 'localtime', 'ABC']
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
    'defaults': {
        'public': {
            ('orders', 'id'): "nextval('orders_id_seq'::regclass)",
            ('orders', 'datestamp'): "now()",
            ('orders', 'status'): "'PENDING'::text",
        }
    },
}

testdata = MetaData(metadata)
cased_schemas = [schema(x) for x in ('public', 'blog', 'CUSTOM', '"Custom"')]
casing = ('SELECT', 'Orders', 'User_Emails', 'CUSTOM', 'Func1', 'Entries',
          'Tags', 'EntryTags', 'EntAccLog',
          'EntryID', 'EntryTitle', 'EntryText')
completers = testdata.get_completers(casing)


@parametrize('completer', completers(filtr=True, casing=False, qualify=no_qual))
@parametrize('table', ['users', '"users"'])
def test_suggested_column_names_from_shadowed_visible_table(completer, table) :
    result = result_set(completer, 'SELECT  FROM ' + table, len('SELECT '))
    assert result == set(testdata.columns_functions_and_keywords('users'))


@parametrize('completer', completers(filtr=True, casing=False, qualify=no_qual))
@parametrize('text', [
    'SELECT  from custom.users',
    'WITH users as (SELECT 1 AS foo) SELECT  from custom.users',
])
def test_suggested_column_names_from_qualified_shadowed_table(completer, text):
    result = result_set(completer, text, position = text.find('  ') + 1)
    assert result == set(testdata.columns_functions_and_keywords(
        'users', 'custom'
    ))


@parametrize('completer', completers(filtr=True, casing=False, qualify=no_qual))
@parametrize('text', ['WITH users as (SELECT 1 AS foo) SELECT  from users',])
def test_suggested_column_names_from_cte(completer, text):
    result = result_set(completer, text, text.find('  ') + 1)
    assert result == set([column('foo')] + testdata.functions_and_keywords())


@parametrize('completer', completers(casing=False))
@parametrize('text', [
    'SELECT * FROM users JOIN custom.shipments ON ',
    '''SELECT *
    FROM public.users
    JOIN custom.shipments ON '''
])
def test_suggested_join_conditions(completer, text):
    result = result_set(completer, text)
    assert result == set([
        alias('users'),
        alias('shipments'),
        name_join('shipments.id = users.id'),
        fk_join('shipments.user_id = users.id')])


@parametrize('completer', completers(filtr=True, casing=False, aliasing=False))
@parametrize(('query', 'tbl'), itertools.product((
    'SELECT * FROM public.{0} RIGHT OUTER JOIN ',
    '''SELECT *
    FROM {0}
    JOIN '''
), ('users', '"users"', 'Users')))
def test_suggested_joins(completer, query, tbl):
    result = result_set(completer, query.format(tbl))
    assert result == set(
        testdata.schemas_and_from_clause_items() +
        [join('custom.shipments ON shipments.user_id = {0}.id'.format(tbl))]
    )


@parametrize('completer', completers(filtr=True, casing=False, qualify=no_qual))
def test_suggested_column_names_from_schema_qualifed_table(completer):
    result = result_set(
        completer, 'SELECT  from custom.products', len('SELECT ')
    )
    assert result == set(testdata.columns_functions_and_keywords(
        'products', 'custom'
    ))


@parametrize('text', [
    'INSERT INTO orders(',
    'INSERT INTO orders (',
    'INSERT INTO public.orders(',
    'INSERT INTO public.orders ('
])
@parametrize('completer', completers(filtr=True, casing=False))
def test_suggested_columns_with_insert(completer, text):
    assert result_set(completer, text) == set(testdata.columns('orders'))


@parametrize('completer', completers(filtr=True, casing=False, qualify=no_qual))
def test_suggested_column_names_in_function(completer):
    result = result_set(
        completer, 'SELECT MAX( from custom.products', len('SELECT MAX(')
    )
    assert result == set(testdata.columns('products', 'custom'))


@parametrize('completer', completers(casing=False, aliasing=False))
@parametrize('text', [
    'SELECT * FROM Custom.',
    'SELECT * FROM custom.',
    'SELECT * FROM "custom".',
])
@parametrize('use_leading_double_quote', [False, True])
def test_suggested_table_names_with_schema_dot(
    completer, text, use_leading_double_quote
):
    if use_leading_double_quote:
        text += '"'
        start_position = -1
    else:
        start_position = 0

    result = result_set(completer, text)
    assert result == set(testdata.from_clause_items('custom', start_position))


@parametrize('completer', completers(casing=False, aliasing=False))
@parametrize('text', [
    'SELECT * FROM "Custom".',
])
@parametrize('use_leading_double_quote', [False, True])
def test_suggested_table_names_with_schema_dot2(
    completer, text, use_leading_double_quote
):
    if use_leading_double_quote:
        text += '"'
        start_position = -1
    else:
        start_position = 0

    result = result_set(completer, text)
    assert result == set(testdata.from_clause_items('Custom', start_position))


@parametrize('completer', completers(filtr=True, casing=False))
def test_suggested_column_names_with_qualified_alias(completer):
    result = result_set(
        completer, 'SELECT p. from custom.products p', len('SELECT p.')
    )
    assert result == set(testdata.columns('products', 'custom'))


@parametrize('completer', completers(filtr=True, casing=False, qualify=no_qual))
def test_suggested_multiple_column_names(completer):
    result = result_set(
        completer, 'SELECT id,  from custom.products', len('SELECT id, ')
    )
    assert result == set(testdata.columns_functions_and_keywords(
        'products', 'custom'
    ))


@parametrize('completer', completers(filtr=True, casing=False))
def test_suggested_multiple_column_names_with_alias(completer):
    result = result_set(
        completer,
        'SELECT p.id, p. from custom.products p',
        len('SELECT u.id, u.')
    )
    assert result == set(testdata.columns('products', 'custom'))


@parametrize('completer', completers(filtr=True, casing=False))
@parametrize('text', [
    'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON ',
    'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON JOIN public.orders z ON z.id > y.id'
])
def test_suggestions_after_on(completer, text):
    position = len('SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON ')
    result = result_set(completer, text, position)
    assert result == set([
        alias('x'),
        alias('y'),
        name_join('y.price = x.price'),
        name_join('y.product_name = x.product_name'),
        name_join('y.id = x.id')])


@parametrize('completer', completers())
def test_suggested_aliases_after_on_right_side(completer):
    text = 'SELECT x.id, y.product_name FROM custom.products x JOIN custom.products y ON x.id = '
    result = result_set(completer, text)
    assert result == set([alias('x'), alias('y')])


@parametrize('completer', completers(filtr=True, casing=False, aliasing=False))
def test_table_names_after_from(completer):
    text = 'SELECT * FROM '
    result = result_set(completer, text)
    assert result == set(testdata.schemas_and_from_clause_items())


@parametrize('completer', completers(filtr=True, casing=False))
def test_schema_qualified_function_name(completer):
    text = 'SELECT custom.func'
    result = result_set(completer, text)
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
def test_schema_qualified_type_name(completer, text):
    result = result_set(completer, text)
    assert result == set(testdata.types('custom'))


@parametrize('completer', completers(filtr=True, casing=False))
def test_suggest_columns_from_aliased_set_returning_function(completer):
    result = result_set(
        completer,
        'select f. from custom.set_returning_func() f',
        len('select f.')
    )
    assert result == set(
        testdata.columns('set_returning_func', 'custom', 'functions'))


@parametrize('completer',completers(filtr=True, casing=False, qualify=no_qual))
@parametrize('text', [
    'SELECT * FROM custom.set_returning_func()',
    'SELECT * FROM Custom.set_returning_func()',
    'SELECT * FROM Custom.Set_Returning_Func()'
])
def test_wildcard_column_expansion_with_function(completer, text):
    position = len('SELECT *')

    completions = get_result(completer, text, position)

    col_list = 'x'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize('completer', completers(filtr=True, casing=False))
def test_wildcard_column_expansion_with_alias_qualifier(completer):
    text = 'SELECT p.* FROM custom.products p'
    position = len('SELECT p.*')

    completions = get_result(completer, text, position)

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
def test_wildcard_column_expansion_with_insert(completer, text):
    position = text.index('*') + 1
    completions = get_result(completer, text, position)

    expected = [wildcard_expansion('ordered_date, status')]
    assert expected == completions


@parametrize('completer', completers(filtr=True, casing=False))
def test_wildcard_column_expansion_with_table_qualifier(completer):
    text = 'SELECT "select".* FROM public."select"'
    position = len('SELECT "select".*')

    completions = get_result(completer, text, position)

    col_list = 'id, "select"."localtime", "select"."ABC"'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize('completer',completers(filtr=True, casing=False, qualify=qual))
def test_wildcard_column_expansion_with_two_tables(completer):
    text = 'SELECT * FROM public."select" JOIN custom.users ON true'
    position = len('SELECT *')

    completions = get_result(completer, text, position)

    cols = ('"select".id, "select"."localtime", "select"."ABC", '
        'users.id, users.phone_number')
    expected = [wildcard_expansion(cols)]
    assert completions == expected


@parametrize('completer', completers(filtr=True, casing=False))
def test_wildcard_column_expansion_with_two_tables_and_parent(completer):
    text = 'SELECT "select".* FROM public."select" JOIN custom.users u ON true'
    position = len('SELECT "select".*')

    completions = get_result(completer, text, position)

    col_list = 'id, "select"."localtime", "select"."ABC"'
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
def test_suggest_columns_from_unquoted_table(completer, text):
    position = len('SELECT U.')
    result = result_set(completer, text, position)
    assert result == set(testdata.columns('users', 'custom'))


@parametrize('completer', completers(filtr=True, casing=False))
@parametrize('text', [
    'SELECT U. FROM custom."Users" U',
    'SELECT U. FROM "custom"."Users" U'
])
def test_suggest_columns_from_quoted_table(completer, text):
    position = len('SELECT U.')
    result = result_set(completer, text, position)
    assert result == set(testdata.columns('Users', 'custom'))

texts = ['SELECT * FROM ', 'SELECT * FROM public.Orders O CROSS JOIN ']


@parametrize('completer', completers(filtr=True, casing=False, aliasing=False))
@parametrize('text', texts)
def test_schema_or_visible_table_completion(completer, text):
    result = result_set(completer, text)
    assert result == set(testdata.schemas_and_from_clause_items())


@parametrize('completer', completers(aliasing=True, casing=False, filtr=True))
@parametrize('text', texts)
def test_table_aliases(completer, text):
    result = result_set(completer, text)
    assert result == set(testdata.schemas() + [
        table('users u'),
        table('orders o' if text == 'SELECT * FROM ' else 'orders o2'),
        table('"select" s'),
        function('func1() f'),
        function('func2() f')])


@parametrize('completer', completers(aliasing=True, casing=True, filtr=True))
@parametrize('text', texts)
def test_aliases_with_casing(completer, text):
    result = result_set(completer, text)
    assert result == set(cased_schemas + [
        table('users u'),
        table('Orders O' if text == 'SELECT * FROM ' else 'Orders O2'),
        table('"select" s'),
        function('Func1() F'),
        function('func2() f')])


@parametrize('completer', completers(aliasing=False, casing=True, filtr=True))
@parametrize('text', texts)
def test_table_casing(completer, text):
    result = result_set(completer, text)
    assert result == set(cased_schemas + [
        table('users'),
        table('Orders'),
        table('"select"'),
        function('Func1()'),
        function('func2()')])


@parametrize('completer', completers(aliasing=False, casing=True))
def test_alias_search_without_aliases2(completer):
    text = 'SELECT * FROM blog.et'
    result = get_result(completer, text)
    assert result[0] == table('EntryTags', -2)


@parametrize('completer', completers(aliasing=False, casing=True))
def test_alias_search_without_aliases1(completer):
    text = 'SELECT * FROM blog.e'
    result = get_result(completer, text)
    assert result[0] == table('Entries', -1)


@parametrize('completer', completers(aliasing=True, casing=True))
def test_alias_search_with_aliases2(completer):
    text = 'SELECT * FROM blog.et'
    result = get_result(completer, text)
    assert result[0] == table('EntryTags ET', -2)


@parametrize('completer', completers(aliasing=True, casing=True))
def test_alias_search_with_aliases1(completer):
    text = 'SELECT * FROM blog.e'
    result = get_result(completer, text)
    assert result[0] == table('Entries E', -1)


@parametrize('completer', completers(aliasing=True, casing=True))
def test_join_alias_search_with_aliases1(completer):
    text = 'SELECT * FROM blog.Entries E JOIN blog.e'
    result = get_result(completer, text)
    assert result[:2] == [table('Entries E2', -1), join(
        'EntAccLog EAL ON EAL.EntryID = E.EntryID', -1)]


@parametrize('completer', completers(aliasing=False, casing=True))
def test_join_alias_search_without_aliases1(completer):
    text = 'SELECT * FROM blog.Entries JOIN blog.e'
    result = get_result(completer, text)
    assert result[:2] == [table('Entries', -1), join(
        'EntAccLog ON EntAccLog.EntryID = Entries.EntryID', -1)]


@parametrize('completer', completers(aliasing=True, casing=True))
def test_join_alias_search_with_aliases2(completer):
    text = 'SELECT * FROM blog.Entries E JOIN blog.et'
    result = get_result(completer, text)
    assert result[0] == join('EntryTags ET ON ET.EntryID = E.EntryID', -2)


@parametrize('completer', completers(aliasing=False, casing=True))
def test_join_alias_search_without_aliases2(completer):
    text = 'SELECT * FROM blog.Entries JOIN blog.et'
    result = get_result(completer, text)
    assert result[0] == join(
        'EntryTags ON EntryTags.EntryID = Entries.EntryID', -2)


@parametrize('completer', completers())
def test_function_alias_search_without_aliases(completer):
    text = 'SELECT blog.ees'
    result = get_result(completer, text)
    first = result[0]
    assert first.start_position == -3
    assert first.text == 'extract_entry_symbols()'
    assert first.display == 'extract_entry_symbols(_entryid)'


@parametrize('completer', completers())
def test_function_alias_search_with_aliases(completer):
    text = 'SELECT blog.ee'
    result = get_result(completer, text)
    first = result[0]
    assert first.start_position == -2
    assert first.text == 'enter_entry(_title := , _text := )'
    assert first.display == 'enter_entry(_title, _text)'


@parametrize('completer',completers(filtr=True, casing=True, qualify=no_qual))
def test_column_alias_search(completer):
    result = get_result(
        completer, 'SELECT et FROM blog.Entries E', len('SELECT et')
    )
    cols = ('EntryText', 'EntryTitle', 'EntryID')
    assert result[:3] == [column(c, -2) for c in cols]


@parametrize('completer', completers(casing=True))
def test_column_alias_search_qualified(completer):
    result = get_result(
        completer, 'SELECT E.ei FROM blog.Entries E', len('SELECT E.ei')
    )
    cols = ('EntryID', 'EntryTitle')
    assert result[:3] == [column(c, -2) for c in cols]


@parametrize('completer', completers(casing=False, filtr=False, aliasing=False))
def test_schema_object_order(completer):
    result = get_result(completer, 'SELECT * FROM u')
    assert result[:3] == [
        table(t, pos=-1) for t in ('users', 'custom."Users"', 'custom.users')
    ]


@parametrize('completer', completers(casing=False, filtr=False, aliasing=False))
def test_all_schema_objects(completer):
    text = ('SELECT * FROM ')
    result = result_set(completer, text)
    assert result >= set(
        [table(x) for x in ('orders', '"select"', 'custom.shipments')]
        + [function(x+'()') for x in ('func2', 'custom.func3')]
    )


@parametrize('completer', completers(filtr=False, aliasing=False, casing=True))
def test_all_schema_objects_with_casing(completer):
    text = 'SELECT * FROM '
    result = result_set(completer, text)
    assert result >= set(
        [table(x) for x in ('Orders', '"select"', 'CUSTOM.shipments')]
        + [function(x+'()') for x in ('func2', 'CUSTOM.func3')]
    )


@parametrize('completer', completers(casing=False, filtr=False, aliasing=True))
def test_all_schema_objects_with_aliases(completer):
    text = ('SELECT * FROM ')
    result = result_set(completer, text)
    assert result >= set(
        [table(x) for x in ('orders o', '"select" s', 'custom.shipments s')]
        + [function(x) for x in ('func2() f', 'custom.func3() f')]
    )


@parametrize('completer', completers(casing=False, filtr=False, aliasing=True))
def test_set_schema(completer):
    text = ('SET SCHEMA ')
    result = result_set(completer, text)
    assert result == set([
        schema(u"'blog'"),
        schema(u"'Custom'"),
        schema(u"'custom'"),
        schema(u"'public'")])
