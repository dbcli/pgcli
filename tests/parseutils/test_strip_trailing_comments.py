"""Dropping the comments that trail a statement.

sqlparse cannot do this for PostgreSQL: it follows MySQL and reads ``#`` as a
comment marker, while in PostgreSQL ``#`` is the bitwise XOR operator. That is
dbcli/pgcli issue #1646 and andialbrecht/sqlparse issue #539: `select 17 # 5`
silently returns 17 instead of 20.
"""

from pgcli.packages.parseutils import strip_trailing_comments


def test_hash_is_an_operator_not_a_comment():
    """The reported bug: everything after # was dropped."""
    assert strip_trailing_comments("select 17 # 5") == "select 17 # 5"
    assert strip_trailing_comments("select 17 # 5;") == "select 17 # 5;"


def test_hash_keeps_its_own_trailing_comment_separate():
    assert strip_trailing_comments("select 17 # 5; -- note") == "select 17 # 5;"


def test_trailing_line_comment_is_dropped():
    """What #1559 fixed: rstrip(';') needs the comment gone first."""
    assert strip_trailing_comments("vacuum freeze verbose t; -- 82% towards emergency") == "vacuum freeze verbose t;"


def test_trailing_block_comment_is_dropped():
    assert strip_trailing_comments("select 1; /* done */") == "select 1;"


def test_nested_block_comments():
    """PostgreSQL block comments nest, unlike C."""
    assert strip_trailing_comments("select 1; /* a /* b */ c */") == "select 1;"


def test_several_trailing_comments():
    assert strip_trailing_comments("select 1;\n-- one\n/* two */\n-- three") == "select 1;"


def test_comments_in_the_middle_are_kept():
    """Only trailing comments go: the server should see the rest as written."""
    for sql in ("select 1, /* keep */ 2;", "select 1\n-- keep\n, 2;"):
        assert strip_trailing_comments(sql) == sql


def test_comment_markers_inside_strings_are_text():
    for sql in ("select '-- not a comment';", "select 'a /* b */ c';", "select 'a # b';"):
        assert strip_trailing_comments(sql) == sql


def test_doubled_quotes_inside_strings():
    sql = "select 'it''s -- fine';"
    assert strip_trailing_comments(sql) == sql


def test_quoted_identifiers():
    sql = 'select 1 as "-- odd name";'
    assert strip_trailing_comments(sql) == sql


def test_dollar_quoted_body_is_left_alone():
    """A function body holds its own comments and must survive intact."""
    sql = "do $$ begin -- inside\n perform 1; end $$;"
    assert strip_trailing_comments(sql) == sql
    tagged = "create function f() returns int as $body$ select 1; -- inner\n$body$ language sql;"
    assert strip_trailing_comments(tagged) == tagged


def test_only_a_comment_leaves_nothing():
    assert strip_trailing_comments("-- just a note") == ""
    assert strip_trailing_comments("/* just a note */") == ""


def test_empty_and_whitespace():
    assert strip_trailing_comments("") == ""
    assert strip_trailing_comments("   \n  ") == ""


def test_unterminated_block_comment_is_kept():
    """PostgreSQL rejects it ("unterminated /* comment"). Dropping it would run
    a different statement and return an answer where the server gave an error:
    `select 4/*2` would quietly say 4."""
    for sql in ("select 1; /* never closed", "select 4/*2"):
        assert strip_trailing_comments(sql) == sql


def test_unterminated_string_does_not_hang():
    assert strip_trailing_comments("select 'never closed") == "select 'never closed"


# --- PostgreSQL operators that look like comment markers -------------------
#
# Every expectation below was run against PostgreSQL 17 first; the value in the
# comment is what the server answers for that expression.


def test_hash_operators_are_left_alone():
    """# starts several operators, none of them a comment."""
    for sql in (
        "select 17 # 5",  # 20, bitwise XOR
        """select '{"a":{"b":7}}'::jsonb #> '{a,b}'""",  # 7, path extract
        """select '{"a":1}'::jsonb #>> '{a}'""",  # 1, path extract as text
        """select '{"a":1,"b":2}'::jsonb #- '{a}'""",  # {"b": 2}, delete path
        "select point '(0,0)' ## lseg '((1,1),(2,2))'",  # (1,1), closest point
        "select box '((0,0),(2,2))' # box '((1,1),(3,3))'",  # intersection
        "select # path '((1,1),(2,2),(3,3))'",  # 3, number of points
    ):
        assert strip_trailing_comments(sql) == sql, sql


def test_operators_built_from_dashes_and_slashes():
    for sql in (
        "select 5 - -3",  # 8, unary minus after an operator
        "select @ -5",  # 5, absolute value
        """select '{"a":1}'::json ->> 'a'""",  # 1
        "select 1 << 3",  # 8
        "select 'abc' ~ 'b'",  # t, regex match
        """select '{"a":1}'::jsonb @> '{"a":1}'""",  # t, contains
        "select 'a' || 'b'",  # ab
    ):
        assert strip_trailing_comments(sql) == sql, sql


def test_double_dash_without_spaces_is_a_comment_to_postgres_too():
    """`select 5--3` answers 5, not 8: the server reads --3 as a comment, so
    dropping it here matches what the server would have done."""
    assert strip_trailing_comments("select 5--3") == "select 5"


def test_hash_inside_a_trailing_comment_is_still_a_comment():
    assert strip_trailing_comments("select 1; -- see issue #1646") == "select 1;"
