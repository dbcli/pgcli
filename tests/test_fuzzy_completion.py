from __future__ import unicode_literals
import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document


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
