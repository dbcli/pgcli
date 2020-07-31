from metadata import (
    MetaData,
    alias,
    name_join,
    fk_join,
    join,
    keyword,
    schema,
    table,
    view,
    function,
    column,
    wildcard_expansion,
    get_result,
    result_set,
    qual,
    no_qual,
    parametrize,
)
from prompt_toolkit.completion import Completion
from utils import completions_to_set


metadata = {
    "tables": {
        "users": ["id", "parentid", "email", "first_name", "last_name"],
        "Users": ["userid", "username"],
        "orders": ["id", "ordered_date", "status", "email"],
        "select": ["id", "insert", "ABC"],
    },
    "views": {"user_emails": ["id", "email"], "functions": ["function"]},
    "functions": [
        ["custom_fun", [], [], [], "", False, False, False, False],
        ["_custom_fun", [], [], [], "", False, False, False, False],
        ["custom_func1", [], [], [], "", False, False, False, False],
        ["custom_func2", [], [], [], "", False, False, False, False],
        [
            "set_returning_func",
            ["x", "y"],
            ["integer", "integer"],
            ["b", "b"],
            "",
            False,
            False,
            True,
            False,
        ],
    ],
    "datatypes": ["custom_type1", "custom_type2"],
    "foreignkeys": [
        ("public", "users", "id", "public", "users", "parentid"),
        ("public", "users", "id", "public", "Users", "userid"),
    ],
}

metadata = dict((k, {"public": v}) for k, v in metadata.items())

testdata = MetaData(metadata)

cased_users_col_names = ["ID", "PARENTID", "Email", "First_Name", "last_name"]
cased_users2_col_names = ["UserID", "UserName"]
cased_func_names = [
    "Custom_Fun",
    "_custom_fun",
    "Custom_Func1",
    "custom_func2",
    "set_returning_func",
]
cased_tbls = ["Users", "Orders"]
cased_views = ["User_Emails", "Functions"]
casing = (
    ["SELECT", "PUBLIC"]
    + cased_func_names
    + cased_tbls
    + cased_views
    + cased_users_col_names
    + cased_users2_col_names
)
# Lists for use in assertions
cased_funcs = [
    function(f)
    for f in ("Custom_Fun()", "_custom_fun()", "Custom_Func1()", "custom_func2()")
] + [function("set_returning_func(x := , y := )", display="set_returning_func(x, y)")]
cased_tbls = [table(t) for t in (cased_tbls + ['"Users"', '"select"'])]
cased_rels = [view(t) for t in cased_views] + cased_funcs + cased_tbls
cased_users_cols = [column(c) for c in cased_users_col_names]
aliased_rels = (
    [table(t) for t in ("users u", '"Users" U', "orders o", '"select" s')]
    + [view("user_emails ue"), view("functions f")]
    + [
        function(f)
        for f in (
            "_custom_fun() cf",
            "custom_fun() cf",
            "custom_func1() cf",
            "custom_func2() cf",
        )
    ]
    + [
        function(
            "set_returning_func(x := , y := ) srf",
            display="set_returning_func(x, y) srf",
        )
    ]
)
cased_aliased_rels = (
    [table(t) for t in ("Users U", '"Users" U', "Orders O", '"select" s')]
    + [view("User_Emails UE"), view("Functions F")]
    + [
        function(f)
        for f in (
            "_custom_fun() cf",
            "Custom_Fun() CF",
            "Custom_Func1() CF",
            "custom_func2() cf",
        )
    ]
    + [
        function(
            "set_returning_func(x := , y := ) srf",
            display="set_returning_func(x, y) srf",
        )
    ]
)
completers = testdata.get_completers(casing)


# Just to make sure that this doesn't crash
@parametrize("completer", completers())
def test_function_column_name(completer):
    for l in range(
        len("SELECT * FROM Functions WHERE function:"),
        len("SELECT * FROM Functions WHERE function:text") + 1,
    ):
        assert [] == get_result(
            completer, "SELECT * FROM Functions WHERE function:text"[:l]
        )


@parametrize("action", ["ALTER", "DROP", "CREATE", "CREATE OR REPLACE"])
@parametrize("completer", completers())
def test_drop_alter_function(completer, action):
    assert get_result(completer, action + " FUNCTION set_ret") == [
        function("set_returning_func(x integer, y integer)", -len("set_ret"))
    ]


@parametrize("completer", completers())
def test_empty_string_completion(completer):
    result = get_result(completer, "")
    assert completions_to_set(
        testdata.keywords() + testdata.specials()
    ) == completions_to_set(result)


@parametrize("completer", completers())
def test_select_keyword_completion(completer):
    result = get_result(completer, "SEL")
    assert completions_to_set(result) == completions_to_set([keyword("SELECT", -3)])


@parametrize("completer", completers())
def test_builtin_function_name_completion(completer):
    result = get_result(completer, "SELECT MA")
    assert completions_to_set(result) == completions_to_set(
        [
            function("MAKE_DATE", -2),
            function("MAKE_INTERVAL", -2),
            function("MAKE_TIME", -2),
            function("MAKE_TIMESTAMP", -2),
            function("MAKE_TIMESTAMPTZ", -2),
            function("MASKLEN", -2),
            function("MAX", -2),
            keyword("MAXEXTENTS", -2),
            keyword("MATERIALIZED VIEW", -2),
        ]
    )


@parametrize("completer", completers())
def test_builtin_function_matches_only_at_start(completer):
    text = "SELECT IN"

    result = [c.text for c in get_result(completer, text)]

    assert "MIN" not in result


@parametrize("completer", completers(casing=False, aliasing=False))
def test_user_function_name_completion(completer):
    result = get_result(completer, "SELECT cu")
    assert completions_to_set(result) == completions_to_set(
        [
            function("custom_fun()", -2),
            function("_custom_fun()", -2),
            function("custom_func1()", -2),
            function("custom_func2()", -2),
            function("CURRENT_DATE", -2),
            function("CURRENT_TIMESTAMP", -2),
            function("CUME_DIST", -2),
            function("CURRENT_TIME", -2),
            keyword("CURRENT", -2),
        ]
    )


@parametrize("completer", completers(casing=False, aliasing=False))
def test_user_function_name_completion_matches_anywhere(completer):
    result = get_result(completer, "SELECT om")
    assert completions_to_set(result) == completions_to_set(
        [
            function("custom_fun()", -2),
            function("_custom_fun()", -2),
            function("custom_func1()", -2),
            function("custom_func2()", -2),
        ]
    )


@parametrize("completer", completers(casing=True))
def test_list_functions_for_special(completer):
    result = get_result(completer, r"\df ")
    assert completions_to_set(result) == completions_to_set(
        [schema("PUBLIC")] + [function(f) for f in cased_func_names]
    )


@parametrize("completer", completers(casing=False, qualify=no_qual))
def test_suggested_column_names_from_visible_table(completer):
    result = get_result(completer, "SELECT  from users", len("SELECT "))
    assert completions_to_set(result) == completions_to_set(
        testdata.columns_functions_and_keywords("users")
    )


@parametrize("completer", completers(casing=True, qualify=no_qual))
def test_suggested_cased_column_names(completer):
    result = get_result(completer, "SELECT  from users", len("SELECT "))
    assert completions_to_set(result) == completions_to_set(
        cased_funcs
        + cased_users_cols
        + testdata.builtin_functions()
        + testdata.keywords()
    )


@parametrize("completer", completers(casing=False, qualify=no_qual))
@parametrize("text", ["SELECT  from users", "INSERT INTO Orders SELECT  from users"])
def test_suggested_auto_qualified_column_names(text, completer):
    position = text.index("  ") + 1
    cols = [column(c.lower()) for c in cased_users_col_names]
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(
        cols + testdata.functions_and_keywords()
    )


@parametrize("completer", completers(casing=False, qualify=qual))
@parametrize(
    "text",
    [
        'SELECT  from users U NATURAL JOIN "Users"',
        'INSERT INTO Orders SELECT  from users U NATURAL JOIN "Users"',
    ],
)
def test_suggested_auto_qualified_column_names_two_tables(text, completer):
    position = text.index("  ") + 1
    cols = [column("U." + c.lower()) for c in cased_users_col_names]
    cols += [column('"Users".' + c.lower()) for c in cased_users2_col_names]
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(
        cols + testdata.functions_and_keywords()
    )


@parametrize("completer", completers(casing=True, qualify=["always"]))
@parametrize("text", ["UPDATE users SET ", "INSERT INTO users("])
def test_no_column_qualification(text, completer):
    cols = [column(c) for c in cased_users_col_names]
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(cols)


@parametrize("completer", completers(casing=True, qualify=["always"]))
def test_suggested_cased_always_qualified_column_names(completer):
    text = "SELECT  from users"
    position = len("SELECT ")
    cols = [column("users." + c) for c in cased_users_col_names]
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(
        cased_funcs + cols + testdata.builtin_functions() + testdata.keywords()
    )


@parametrize("completer", completers(casing=False, qualify=no_qual))
def test_suggested_column_names_in_function(completer):
    result = get_result(completer, "SELECT MAX( from users", len("SELECT MAX("))
    assert completions_to_set(result) == completions_to_set(
        (testdata.columns_functions_and_keywords("users"))
    )


@parametrize("completer", completers(casing=False))
def test_suggested_column_names_with_table_dot(completer):
    result = get_result(completer, "SELECT users. from users", len("SELECT users."))
    assert completions_to_set(result) == completions_to_set(testdata.columns("users"))


@parametrize("completer", completers(casing=False))
def test_suggested_column_names_with_alias(completer):
    result = get_result(completer, "SELECT u. from users u", len("SELECT u."))
    assert completions_to_set(result) == completions_to_set(testdata.columns("users"))


@parametrize("completer", completers(casing=False, qualify=no_qual))
def test_suggested_multiple_column_names(completer):
    result = get_result(completer, "SELECT id,  from users u", len("SELECT id, "))
    assert completions_to_set(result) == completions_to_set(
        (testdata.columns_functions_and_keywords("users"))
    )


@parametrize("completer", completers(casing=False))
def test_suggested_multiple_column_names_with_alias(completer):
    result = get_result(
        completer, "SELECT u.id, u. from users u", len("SELECT u.id, u.")
    )
    assert completions_to_set(result) == completions_to_set(testdata.columns("users"))


@parametrize("completer", completers(casing=True))
def test_suggested_cased_column_names_with_alias(completer):
    result = get_result(
        completer, "SELECT u.id, u. from users u", len("SELECT u.id, u.")
    )
    assert completions_to_set(result) == completions_to_set(cased_users_cols)


@parametrize("completer", completers(casing=False))
def test_suggested_multiple_column_names_with_dot(completer):
    result = get_result(
        completer,
        "SELECT users.id, users. from users u",
        len("SELECT users.id, users."),
    )
    assert completions_to_set(result) == completions_to_set(testdata.columns("users"))


@parametrize("completer", completers(casing=False))
def test_suggest_columns_after_three_way_join(completer):
    text = """SELECT * FROM users u1
              INNER JOIN users u2 ON u1.id = u2.id
              INNER JOIN users u3 ON u2.id = u3."""
    result = get_result(completer, text)
    assert column("id") in result


join_condition_texts = [
    'INSERT INTO orders SELECT * FROM users U JOIN "Users" U2 ON ',
    """INSERT INTO public.orders(orderid)
    SELECT * FROM users U JOIN "Users" U2 ON """,
    'SELECT * FROM users U JOIN "Users" U2 ON ',
    'SELECT * FROM users U INNER join "Users" U2 ON ',
    'SELECT * FROM USERS U right JOIN "Users" U2 ON ',
    'SELECT * FROM users U LEFT JOIN "Users" U2 ON ',
    'SELECT * FROM Users U FULL JOIN "Users" U2 ON ',
    'SELECT * FROM users U right outer join "Users" U2 ON ',
    'SELECT * FROM Users U LEFT OUTER JOIN "Users" U2 ON ',
    'SELECT * FROM users U FULL OUTER JOIN "Users" U2 ON ',
    """SELECT *
    FROM users U
    FULL OUTER JOIN "Users" U2 ON
    """,
]


@parametrize("completer", completers(casing=False))
@parametrize("text", join_condition_texts)
def test_suggested_join_conditions(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [alias("U"), alias("U2"), fk_join("U2.userid = U.id")]
    )


@parametrize("completer", completers(casing=True))
@parametrize("text", join_condition_texts)
def test_cased_join_conditions(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [alias("U"), alias("U2"), fk_join("U2.UserID = U.ID")]
    )


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        """SELECT *
    FROM users
    CROSS JOIN "Users"
    NATURAL JOIN users u
    JOIN "Users" u2 ON
    """
    ],
)
def test_suggested_join_conditions_with_same_table_twice(completer, text):
    result = get_result(completer, text)
    assert result == [
        fk_join("u2.userid = u.id"),
        fk_join("u2.userid = users.id"),
        name_join('u2.userid = "Users".userid'),
        name_join('u2.username = "Users".username'),
        alias("u"),
        alias("u2"),
        alias("users"),
        alias('"Users"'),
    ]


@parametrize("completer", completers())
@parametrize("text", ["SELECT * FROM users JOIN users u2 on foo."])
def test_suggested_join_conditions_with_invalid_qualifier(completer, text):
    result = get_result(completer, text)
    assert result == []


@parametrize("completer", completers(casing=False))
@parametrize(
    ("text", "ref"),
    [
        ("SELECT * FROM users JOIN NonTable on ", "NonTable"),
        ("SELECT * FROM users JOIN nontable nt on ", "nt"),
    ],
)
def test_suggested_join_conditions_with_invalid_table(completer, text, ref):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [alias("users"), alias(ref)]
    )


@parametrize("completer", completers(casing=False, aliasing=False))
@parametrize(
    "text",
    [
        'SELECT * FROM "Users" u JOIN u',
        'SELECT * FROM "Users" u JOIN uid',
        'SELECT * FROM "Users" u JOIN userid',
        'SELECT * FROM "Users" u JOIN id',
    ],
)
def test_suggested_joins_fuzzy(completer, text):
    result = get_result(completer, text)
    last_word = text.split()[-1]
    expected = join("users ON users.id = u.userid", -len(last_word))
    assert expected in result


join_texts = [
    "SELECT * FROM Users JOIN ",
    """INSERT INTO "Users"
    SELECT *
    FROM Users
    INNER JOIN """,
    """INSERT INTO public."Users"(username)
    SELECT *
    FROM Users
    INNER JOIN """,
    """SELECT *
    FROM Users
    INNER JOIN """,
]


@parametrize("completer", completers(casing=False, aliasing=False))
@parametrize("text", join_texts)
def test_suggested_joins(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.schemas_and_from_clause_items()
        + [
            join('"Users" ON "Users".userid = Users.id'),
            join("users users2 ON users2.id = Users.parentid"),
            join("users users2 ON users2.parentid = Users.id"),
        ]
    )


@parametrize("completer", completers(casing=True, aliasing=False))
@parametrize("text", join_texts)
def test_cased_joins(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [schema("PUBLIC")]
        + cased_rels
        + [
            join('"Users" ON "Users".UserID = Users.ID'),
            join("Users Users2 ON Users2.ID = Users.PARENTID"),
            join("Users Users2 ON Users2.PARENTID = Users.ID"),
        ]
    )


@parametrize("completer", completers(casing=False, aliasing=True))
@parametrize("text", join_texts)
def test_aliased_joins(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.schemas()
        + aliased_rels
        + [
            join('"Users" U ON U.userid = Users.id'),
            join("users u ON u.id = Users.parentid"),
            join("users u ON u.parentid = Users.id"),
        ]
    )


@parametrize("completer", completers(casing=False, aliasing=False))
@parametrize(
    "text",
    [
        'SELECT * FROM public."Users" JOIN ',
        'SELECT * FROM public."Users" RIGHT OUTER JOIN ',
        """SELECT *
    FROM public."Users"
    LEFT JOIN """,
    ],
)
def test_suggested_joins_quoted_schema_qualified_table(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.schemas_and_from_clause_items()
        + [join('public.users ON users.id = "Users".userid')]
    )


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "SELECT u.name, o.id FROM users u JOIN orders o ON ",
        "SELECT u.name, o.id FROM users u JOIN orders o ON JOIN orders o2 ON",
    ],
)
def test_suggested_aliases_after_on(completer, text):
    position = len("SELECT u.name, o.id FROM users u JOIN orders o ON ")
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(
        [
            alias("u"),
            name_join("o.id = u.id"),
            name_join("o.email = u.email"),
            alias("o"),
        ]
    )


@parametrize("completer", completers())
@parametrize(
    "text",
    [
        "SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = ",
        "SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id =  JOIN orders o2 ON",
    ],
)
def test_suggested_aliases_after_on_right_side(completer, text):
    position = len("SELECT u.name, o.id FROM users u JOIN orders o ON o.user_id = ")
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set([alias("u"), alias("o")])


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "SELECT users.name, orders.id FROM users JOIN orders ON ",
        "SELECT users.name, orders.id FROM users JOIN orders ON JOIN orders orders2 ON",
    ],
)
def test_suggested_tables_after_on(completer, text):
    position = len("SELECT users.name, orders.id FROM users JOIN orders ON ")
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(
        [
            name_join("orders.id = users.id"),
            name_join("orders.email = users.email"),
            alias("users"),
            alias("orders"),
        ]
    )


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = JOIN orders orders2 ON",
        "SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = ",
    ],
)
def test_suggested_tables_after_on_right_side(completer, text):
    position = len(
        "SELECT users.name, orders.id FROM users JOIN orders ON orders.user_id = "
    )
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(
        [alias("users"), alias("orders")]
    )


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "SELECT * FROM users INNER JOIN orders USING (",
        "SELECT * FROM users INNER JOIN orders USING(",
    ],
)
def test_join_using_suggests_common_columns(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [column("id"), column("email")]
    )


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "SELECT * FROM users u1 JOIN users u2 USING (email) JOIN user_emails ue USING()",
        "SELECT * FROM users u1 JOIN users u2 USING(email) JOIN user_emails ue USING ()",
        "SELECT * FROM users u1 JOIN user_emails ue USING () JOIN users u2 ue USING(first_name, last_name)",
        "SELECT * FROM users u1 JOIN user_emails ue USING() JOIN users u2 ue USING (first_name, last_name)",
    ],
)
def test_join_using_suggests_from_last_table(completer, text):
    position = text.index("()") + 1
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(
        [column("id"), column("email")]
    )


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "SELECT * FROM users INNER JOIN orders USING (id,",
        "SELECT * FROM users INNER JOIN orders USING(id,",
    ],
)
def test_join_using_suggests_columns_after_first_column(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [column("id"), column("email")]
    )


@parametrize("completer", completers(casing=False, aliasing=False))
@parametrize(
    "text",
    [
        "SELECT * FROM ",
        "SELECT * FROM users CROSS JOIN ",
        "SELECT * FROM users natural join ",
    ],
)
def test_table_names_after_from(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.schemas_and_from_clause_items()
    )
    assert [c.text for c in result] == [
        "public",
        "orders",
        '"select"',
        "users",
        '"Users"',
        "functions",
        "user_emails",
        "_custom_fun()",
        "custom_fun()",
        "custom_func1()",
        "custom_func2()",
        "set_returning_func(x := , y := )",
    ]


@parametrize("completer", completers(casing=False, qualify=no_qual))
def test_auto_escaped_col_names(completer):
    result = get_result(completer, 'SELECT  from "select"', len("SELECT "))
    assert completions_to_set(result) == completions_to_set(
        testdata.columns_functions_and_keywords("select")
    )


@parametrize("completer", completers(aliasing=False))
def test_allow_leading_double_quote_in_last_word(completer):
    result = get_result(completer, 'SELECT * from "sele')

    expected = table('"select"', -5)

    assert expected in result


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "SELECT 1::",
        "CREATE TABLE foo (bar ",
        "CREATE FUNCTION foo (bar INT, baz ",
        "ALTER TABLE foo ALTER COLUMN bar TYPE ",
    ],
)
def test_suggest_datatype(text, completer):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.schemas() + testdata.types() + testdata.builtin_datatypes()
    )


@parametrize("completer", completers(casing=False))
def test_suggest_columns_from_escaped_table_alias(completer):
    result = get_result(completer, 'select * from "select" s where s.')
    assert completions_to_set(result) == completions_to_set(testdata.columns("select"))


@parametrize("completer", completers(casing=False, qualify=no_qual))
def test_suggest_columns_from_set_returning_function(completer):
    result = get_result(completer, "select  from set_returning_func()", len("select "))
    assert completions_to_set(result) == completions_to_set(
        testdata.columns_functions_and_keywords("set_returning_func", typ="functions")
    )


@parametrize("completer", completers(casing=False))
def test_suggest_columns_from_aliased_set_returning_function(completer):
    result = get_result(
        completer, "select f. from set_returning_func() f", len("select f.")
    )
    assert completions_to_set(result) == completions_to_set(
        testdata.columns("set_returning_func", typ="functions")
    )


@parametrize("completer", completers(casing=False))
def test_join_functions_using_suggests_common_columns(completer):
    text = """SELECT * FROM set_returning_func() f1
              INNER JOIN set_returning_func() f2 USING ("""
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.columns("set_returning_func", typ="functions")
    )


@parametrize("completer", completers(casing=False))
def test_join_functions_on_suggests_columns_and_join_conditions(completer):
    text = """SELECT * FROM set_returning_func() f1
              INNER JOIN set_returning_func() f2 ON f1."""
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [name_join("y = f2.y"), name_join("x = f2.x")]
        + testdata.columns("set_returning_func", typ="functions")
    )


@parametrize("completer", completers())
def test_learn_keywords(completer):
    history = "CREATE VIEW v AS SELECT 1"
    completer.extend_query_history(history)

    # Now that we've used `VIEW` once, it should be suggested ahead of other
    # keywords starting with v.
    text = "create v"
    completions = get_result(completer, text)
    assert completions[0].text == "VIEW"


@parametrize("completer", completers(casing=False, aliasing=False))
def test_learn_table_names(completer):
    history = "SELECT * FROM users; SELECT * FROM orders; SELECT * FROM users"
    completer.extend_query_history(history)

    text = "SELECT * FROM "
    completions = get_result(completer, text)

    # `users` should be higher priority than `orders` (used more often)
    users = table("users")
    orders = table("orders")

    assert completions.index(users) < completions.index(orders)


@parametrize("completer", completers(casing=False, qualify=no_qual))
def test_columns_before_keywords(completer):
    text = "SELECT * FROM orders WHERE s"
    completions = get_result(completer, text)

    col = column("status", -1)
    kw = keyword("SELECT", -1)

    assert completions.index(col) < completions.index(kw)


@parametrize("completer", completers(casing=False, qualify=no_qual))
@parametrize(
    "text",
    [
        "SELECT * FROM users",
        "INSERT INTO users SELECT * FROM users u",
        """INSERT INTO users(id, parentid, email, first_name, last_name)
    SELECT *
    FROM users u""",
    ],
)
def test_wildcard_column_expansion(completer, text):
    position = text.find("*") + 1

    completions = get_result(completer, text, position)

    col_list = "id, parentid, email, first_name, last_name"
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "SELECT u.* FROM users u",
        "INSERT INTO public.users SELECT u.* FROM users u",
        """INSERT INTO users(id, parentid, email, first_name, last_name)
    SELECT u.*
    FROM users u""",
    ],
)
def test_wildcard_column_expansion_with_alias(completer, text):
    position = text.find("*") + 1

    completions = get_result(completer, text, position)

    col_list = "id, u.parentid, u.email, u.first_name, u.last_name"
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize("completer", completers(casing=False))
@parametrize(
    "text,expected",
    [
        (
            "SELECT users.* FROM users",
            "id, users.parentid, users.email, users.first_name, users.last_name",
        ),
        (
            "SELECT Users.* FROM Users",
            "id, Users.parentid, Users.email, Users.first_name, Users.last_name",
        ),
    ],
)
def test_wildcard_column_expansion_with_table_qualifier(completer, text, expected):
    position = len("SELECT users.*")

    completions = get_result(completer, text, position)

    expected = [wildcard_expansion(expected)]

    assert expected == completions


@parametrize("completer", completers(casing=False, qualify=qual))
def test_wildcard_column_expansion_with_two_tables(completer):
    text = 'SELECT * FROM "select" JOIN users u ON true'
    position = len("SELECT *")

    completions = get_result(completer, text, position)

    cols = (
        '"select".id, "select".insert, "select"."ABC", '
        "u.id, u.parentid, u.email, u.first_name, u.last_name"
    )
    expected = [wildcard_expansion(cols)]
    assert completions == expected


@parametrize("completer", completers(casing=False))
def test_wildcard_column_expansion_with_two_tables_and_parent(completer):
    text = 'SELECT "select".* FROM "select" JOIN users u ON true'
    position = len('SELECT "select".*')

    completions = get_result(completer, text, position)

    col_list = 'id, "select".insert, "select"."ABC"'
    expected = [wildcard_expansion(col_list)]

    assert expected == completions


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    ["SELECT U. FROM Users U", "SELECT U. FROM USERS U", "SELECT U. FROM users U"],
)
def test_suggest_columns_from_unquoted_table(completer, text):
    position = len("SELECT U.")
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(testdata.columns("users"))


@parametrize("completer", completers(casing=False))
def test_suggest_columns_from_quoted_table(completer):
    result = get_result(completer, 'SELECT U. FROM "Users" U', len("SELECT U."))
    assert completions_to_set(result) == completions_to_set(testdata.columns("Users"))


@parametrize("completer", completers(casing=False, aliasing=False))
@parametrize("text", ["SELECT * FROM ", "SELECT * FROM Orders o CROSS JOIN "])
def test_schema_or_visible_table_completion(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.schemas_and_from_clause_items()
    )


@parametrize("completer", completers(casing=False, aliasing=True))
@parametrize("text", ["SELECT * FROM "])
def test_table_aliases(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.schemas() + aliased_rels
    )


@parametrize("completer", completers(casing=False, aliasing=True))
@parametrize("text", ["SELECT * FROM Orders o CROSS JOIN "])
def test_duplicate_table_aliases(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        testdata.schemas()
        + [
            table("orders o2"),
            table("users u"),
            table('"Users" U'),
            table('"select" s'),
            view("user_emails ue"),
            view("functions f"),
            function("_custom_fun() cf"),
            function("custom_fun() cf"),
            function("custom_func1() cf"),
            function("custom_func2() cf"),
            function(
                "set_returning_func(x := , y := ) srf",
                display="set_returning_func(x, y) srf",
            ),
        ]
    )


@parametrize("completer", completers(casing=True, aliasing=True))
@parametrize("text", ["SELECT * FROM Orders o CROSS JOIN "])
def test_duplicate_aliases_with_casing(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [
            schema("PUBLIC"),
            table("Orders O2"),
            table("Users U"),
            table('"Users" U'),
            table('"select" s'),
            view("User_Emails UE"),
            view("Functions F"),
            function("_custom_fun() cf"),
            function("Custom_Fun() CF"),
            function("Custom_Func1() CF"),
            function("custom_func2() cf"),
            function(
                "set_returning_func(x := , y := ) srf",
                display="set_returning_func(x, y) srf",
            ),
        ]
    )


@parametrize("completer", completers(casing=True, aliasing=True))
@parametrize("text", ["SELECT * FROM "])
def test_aliases_with_casing(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [schema("PUBLIC")] + cased_aliased_rels
    )


@parametrize("completer", completers(casing=True, aliasing=False))
@parametrize("text", ["SELECT * FROM "])
def test_table_casing(completer, text):
    result = get_result(completer, text)
    assert completions_to_set(result) == completions_to_set(
        [schema("PUBLIC")] + cased_rels
    )


@parametrize("completer", completers(casing=False))
@parametrize(
    "text",
    [
        "INSERT INTO users ()",
        "INSERT INTO users()",
        "INSERT INTO users () SELECT * FROM orders;",
        "INSERT INTO users() SELECT * FROM users u cross join orders o",
    ],
)
def test_insert(completer, text):
    position = text.find("(") + 1
    result = get_result(completer, text, position)
    assert completions_to_set(result) == completions_to_set(testdata.columns("users"))


@parametrize("completer", completers(casing=False, aliasing=False))
def test_suggest_cte_names(completer):
    text = """
        WITH cte1 AS (SELECT a, b, c FROM foo),
             cte2 AS (SELECT d, e, f FROM bar)
        SELECT * FROM
    """
    result = get_result(completer, text)
    expected = completions_to_set(
        [
            Completion("cte1", 0, display_meta="table"),
            Completion("cte2", 0, display_meta="table"),
        ]
    )
    assert expected <= completions_to_set(result)


@parametrize("completer", completers(casing=False, qualify=no_qual))
def test_suggest_columns_from_cte(completer):
    result = get_result(
        completer,
        "WITH cte AS (SELECT foo, bar FROM baz) SELECT  FROM cte",
        len("WITH cte AS (SELECT foo, bar FROM baz) SELECT "),
    )
    expected = [
        Completion("foo", 0, display_meta="column"),
        Completion("bar", 0, display_meta="column"),
    ] + testdata.functions_and_keywords()

    assert completions_to_set(expected) == completions_to_set(result)


@parametrize("completer", completers(casing=False, qualify=no_qual))
@parametrize(
    "text",
    [
        "WITH cte AS (SELECT foo FROM bar) SELECT * FROM cte WHERE cte.",
        "WITH cte AS (SELECT foo FROM bar) SELECT * FROM cte c WHERE c.",
    ],
)
def test_cte_qualified_columns(completer, text):
    result = get_result(completer, text)
    expected = [Completion("foo", 0, display_meta="column")]
    assert completions_to_set(expected) == completions_to_set(result)


@parametrize(
    "keyword_casing,expected,texts",
    [
        ("upper", "SELECT", ("", "s", "S", "Sel")),
        ("lower", "select", ("", "s", "S", "Sel")),
        ("auto", "SELECT", ("", "S", "SEL", "seL")),
        ("auto", "select", ("s", "sel", "SEl")),
    ],
)
def test_keyword_casing_upper(keyword_casing, expected, texts):
    for text in texts:
        completer = testdata.get_completer({"keyword_casing": keyword_casing})
        completions = get_result(completer, text)
        assert expected in [cpl.text for cpl in completions]


@parametrize("completer", completers())
def test_keyword_after_alter(completer):
    text = "ALTER TABLE users ALTER "
    expected = Completion("COLUMN", start_position=0, display_meta="keyword")
    completions = get_result(completer, text)
    assert expected in completions


@parametrize("completer", completers())
def test_set_schema(completer):
    text = "SET SCHEMA "
    result = get_result(completer, text)
    expected = completions_to_set([schema("'public'")])
    assert completions_to_set(result) == expected


@parametrize("completer", completers())
def test_special_name_completion(completer):
    result = get_result(completer, "\\t")
    assert completions_to_set(result) == completions_to_set(
        [
            Completion(
                text="\\timing",
                start_position=-2,
                display_meta="Toggle timing of commands.",
            )
        ]
    )
