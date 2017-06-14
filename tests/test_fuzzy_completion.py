from __future__ import unicode_literals
import pytest


@pytest.fixture
def completer():
    import pgcli.pgcompleter as pgcompleter
    return pgcompleter.PGCompleter()


def test_ranking_ignores_identifier_quotes(completer):
    """When calculating result rank, identifier quotes should be ignored.

    The result ranking algorithm ignores identifier quotes. Without this
    correction, the match "user", which Postgres requires to be quoted
    since it is also a reserved word, would incorrectly fall below the
    match user_action because the literal quotation marks in "user"
    alter the position of the match.

    This test checks that the fuzzy ranking algorithm correctly ignores
    quotation marks when computing match ranks.

    """

    text = 'user'
    collection = ['user_action', '"user"']
    matches = completer.find_matches(text, collection)
    assert len(matches) == 2


def test_ranking_based_on_shortest_match(completer):
    """Fuzzy result rank should be based on shortest match.

    Result ranking in fuzzy searching is partially based on the length
    of matches: shorter matches are considered more relevant than
    longer ones. When searching for the text 'user', the length
    component of the match 'user_group' could be either 4 ('user') or
    7 ('user_gr').

    This test checks that the fuzzy ranking algorithm uses the shorter
    match when calculating result rank.

    """

    text = 'user'
    collection = ['api_user', 'user_group']
    matches = completer.find_matches(text, collection)

    assert matches[1].priority > matches[0].priority


@pytest.mark.parametrize('collection', [
    ['user_action', 'user'],
    ['user_group', 'user'],
    ['user_group', 'user_action'],
])
def test_should_break_ties_using_lexical_order(completer, collection):
    """Fuzzy result rank should use lexical order to break ties.

    When fuzzy matching, if multiple matches have the same match length and
    start position, present them in lexical (rather than arbitrary) order. For
    example, if we have tables 'user', 'user_action', and 'user_group', a
    search for the text 'user' should present these tables in this order.

    The input collections to this test are out of order; each run checks that
    the search text 'user' results in the input tables being reordered
    lexically.

    """

    text = 'user'
    matches = completer.find_matches(text, collection)

    assert matches[1].priority > matches[0].priority


def test_matching_should_be_case_insensitive(completer):
    """Fuzzy matching should keep matches even if letter casing doesn't match.

    This test checks that variations of the text which have different casing
    are still matched.
    """

    text = 'foo'
    collection = ['Foo', 'FOO', 'fOO']
    matches = completer.find_matches(text, collection)

    assert len(matches) == 3
