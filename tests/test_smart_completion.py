import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

tables = {
    'users': ['id', 'email', 'first_name', 'last_name'],
    'orders': ['id', 'ordered_date', 'status']
}

@pytest.fixture
def completer():

    import pgcli.pgcompleter as pgcompleter
    comp = pgcompleter.PGCompleter(smart_completion=True)
    comp.extend_table_names(tables.keys())
    for t in tables:
        comp.extend_column_names(t, tables[t])
    return comp

@pytest.fixture
def complete_event():
    from mock import Mock
    return Mock()

def test_empty_string_completion(completer, complete_event):
    text = ''
    position = 0
    result = set(
        completer.get_completions(
            Document(text=text, cursor_position=position),
            complete_event))
    assert set(map(Completion, completer.keywords)) == result

def test_select_keyword_completion(completer, complete_event):
    text = 'SEL'
    position = len('SEL')
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert set(result) == set([Completion(text='SELECT', start_position=-3)])

def test_function_name_completion(completer, complete_event):
    text = 'SELECT MA'
    position = len('SELECT MA')
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert set(result) == set([Completion(text='MAX', start_position=-2)])

def test_suggested_column_names_in_function(completer, complete_event):
    text = 'SELECT MAX( from users'
    position = len('SELECT MAX(')
    result = completer.get_completions(
        Document(text=text, cursor_position=position),
        complete_event)
    assert set(result) == set([
        Completion(text='*', start_position=0),
        Completion(text='id', start_position=0),
        Completion(text='email', start_position=0),
        Completion(text='first_name', start_position=0),
        Completion(text='last_name', start_position=0)])
