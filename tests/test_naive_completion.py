from __future__ import unicode_literals
import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document


@pytest.fixture
def completer():
    import pgcli.pgcompleter as pgcompleter
    return pgcompleter.PGCompleter(smart_completion=False)


@pytest.fixture
def complete_event():
    from mock import Mock
    return Mock()


def test_empty_string_completion(completer, complete_event):
    text = ''
    position = 0
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert result == set(map(Completion, completer.all_completions))


def test_select_keyword_completion(completer, complete_event):
    text = 'SEL'
    position = len('SEL')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert result == set([Completion(text='SELECT', start_position=-3)])


def test_function_name_completion(completer, complete_event):
    text = 'SELECT MA'
    position = len('SELECT MA')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert result == set([
        Completion(text='MATERIALIZED VIEW', start_position=-2),
        Completion(text='MAX', start_position=-2),
        Completion(text='MAXEXTENTS', start_position=-2)])


def test_column_name_completion(completer, complete_event):
    text = 'SELECT  FROM users'
    position = len('SELECT ')
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event))
    assert result == set(map(Completion, completer.all_completions))


def test_paths_completion(completer, complete_event):
    text = '\i '
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event,
        smart_completion=True))
    assert result > set([Completion(text="setup.py", start_position=0)])


def test_alter_well_known_keywords_completion(completer, complete_event):
    text = 'ALTER '
    position = len(text)
    result = set(completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event,
        smart_completion=True))
    assert result > set([
        Completion(text="DATABASE", display_meta='keyword'),
        Completion(text="TABLE", display_meta='keyword'),
        Completion(text="SYSTEM", display_meta='keyword'),
    ])
    assert Completion(text="CREATE", display_meta="keyword") not in result
