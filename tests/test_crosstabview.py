import pytest

from pgcli.crosstabview import CrosstabViewError, crosstabview, parse_args, split_query

HEADERS = ["first", "second", "gt2"]
ROWS = [(1, "one", False), (2, "two", False), (3, "three", True), (4, "four", True)]


def test_split_query():
    assert split_query("select 1") is None
    assert split_query("select 1 \\crosstabview") == ("select 1", "")
    assert split_query("select 1\n\\crosstabview a \"B c\"") == ("select 1", ' a "B c"')
    assert split_query("\\crosstabview 1 2") == ("", " 1 2")
    # inside a string literal
    assert split_query("select 'x \\crosstabview y'") is None


def test_parse_args():
    assert parse_args(' a "B c"  3 "fO""o"') == ["a", '"B c"', "3", '"fO""o"']
    assert parse_args("") == []


def test_defaults():
    # first column vertical, second horizontal, third data
    rows, headers = crosstabview(HEADERS, ROWS, [])
    assert headers == ["first", "one", "two", "three", "four"]
    assert rows == [
        [1, False, "", "", ""],
        [2, "", False, "", ""],
        [3, "", "", True, ""],
        [4, "", "", "", True],
    ]


def test_columns_by_name_and_number():
    rows, headers = crosstabview(HEADERS, ROWS, ["second", "1", "GT2"])
    assert headers == ["second", "1", "2", "3", "4"]
    assert rows[0] == ["one", False, "", "", ""]


def test_quoted_names_are_case_sensitive():
    headers = ["Foo", "b", "c"]
    assert crosstabview(headers, [(1, 2, 3)], ['"Foo"'])[1] == ["Foo", "2"]
    with pytest.raises(CrosstabViewError, match=r'column name not found: "foo"'):
        crosstabview(headers, [(1, 2, 3)], ["Foo"])
    # a quoted number is a name, and "" is an escaped quote
    assert crosstabview(["1", 'fO"o', "c"], [(1, 2, 3)], ['"fO""o"', '"1"'])[1] == ['fO"o', "1"]


def test_sort_column():
    headers = ["a", "b", "c", "s"]
    rows = [("x", "b", 1, "z"), ("x", "a", 2, "-3"), ("y", "c", 3, None), ("y", "d", 3, "1.5"), ("y", "e", 4, "-1")]
    grid, headers = crosstabview(headers, rows, ["a", "b", "c", "s"])
    # integer ranks sort; anything else ranks 0, ties in name order
    assert headers == ["a", "a", "e", "b", "c", "d"]
    assert grid == [["x", 2, "", 1, "", ""], ["y", "", 4, "", 3, 3]]


def test_nulls():
    rows = [(1, 2, None), (1, None, 4), (None, 3, 5), (2, 3, 6)]
    grid, headers = crosstabview(["a", "b", "c"], rows, [])
    # A NULL data value stays None; a cell without data is empty.
    assert headers == ["a", "2", None, "3"]
    assert grid == [[1, None, 4, ""], [None, "", "", 5], [2, "", "", 6]]


@pytest.mark.parametrize(
    "headers, rows, args, message",
    [
        (["a", "b"], [], [], "query must return at least three columns"),
        (["a", "b", "c", "d"], [], [], "data column must be specified when query returns more than three columns"),
        (["a", "b", "c"], [], ["a", "a"], "vertical and horizontal headers must be different columns"),
        (["a", "b", "c"], [], ["5"], r"column number 5 is out of range 1\.\.3"),
        (["a", "b", "c"], [], ["0"], r"column number 0 is out of range 1\.\.3"),
        (["a", "a", "c"], [], ["a"], 'ambiguous column name: "a"'),
        (["a", "b", "c"], [(1, 2, 3), (1, 2, 4)], [], 'multiple data values for row "1", column "2"'),
        (["a", "b", "c"], [(1, None, 3), (1, None, 4)], [], r'multiple data values for row "1", column "\(null\)"'),
        (["a", "b", "c"], [(1, i, 1) for i in range(1601)], [], r"maximum number of columns \(1600\) exceeded"),
    ],
)
def test_errors(headers, rows, args, message):
    with pytest.raises(CrosstabViewError, match=message):
        crosstabview(headers, rows, args)
