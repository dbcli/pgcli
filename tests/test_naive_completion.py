import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document

@pytest.fixture
def completer():
    import pgcli.pgcompleter as pgcompleter
    return pgcompleter.PGCompleter(smart_completion=False)

def test_empty_string_completion(completer):
    #print set(completer.get_completions(Document(text='')))
    #print set(map(Completion, completer.all_completions))
    #assert False
    #assert set(map(Completion, completer.keywords)) == set(completer.get_completions(Document(text='')))
    pass
