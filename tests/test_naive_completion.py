import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
from utils import completions_to_set


@pytest.fixture
def completer():
    import pgcli.pgcompleter as pgcompleter

    return pgcompleter.PGCompleter(smart_completion=False)


@pytest.fixture
def complete_event():
    from mock import Mock

    return Mock()


def test_empty_string_completion(completer, complete_event):
    text = ""
    position = 0
    result = completions_to_set(
        completer.get_completions(
            Document(text=text, cursor_position=position), complete_event
        )
    )
    assert result == completions_to_set(map(Completion, completer.all_completions))


def test_select_keyword_completion(completer, complete_event):
    text = "SEL"
    position = len("SEL")
    result = completions_to_set(
        completer.get_completions(
            Document(text=text, cursor_position=position), complete_event
        )
    )
    assert result == completions_to_set([Completion(text="SELECT", start_position=-3)])


def test_function_name_completion(completer, complete_event):
    text = "SELECT MA"
    position = len("SELECT MA")
    result = completions_to_set(
        completer.get_completions(
            Document(text=text, cursor_position=position), complete_event
        )
    )
    assert result == completions_to_set(
        [
            Completion(text="MATERIALIZED VIEW", start_position=-2),
            Completion(text="MAX", start_position=-2),
            Completion(text="MAXEXTENTS", start_position=-2),
            Completion(text="MAKE_DATE", start_position=-2),
            Completion(text="MAKE_TIME", start_position=-2),
            Completion(text="MAKE_TIMESTAMPTZ", start_position=-2),
            Completion(text="MAKE_INTERVAL", start_position=-2),
            Completion(text="MASKLEN", start_position=-2),
            Completion(text="MAKE_TIMESTAMP", start_position=-2),
        ]
    )


def test_column_name_completion(completer, complete_event):
    text = "SELECT  FROM users"
    position = len("SELECT ")
    result = completions_to_set(
        completer.get_completions(
            Document(text=text, cursor_position=position), complete_event
        )
    )
    assert result == completions_to_set(map(Completion, completer.all_completions))


def test_alter_well_known_keywords_completion(completer, complete_event):
    text = "ALTER "
    position = len(text)
    result = completions_to_set(
        completer.get_completions(
            Document(text=text, cursor_position=position),
            complete_event,
            smart_completion=True,
        )
    )
    assert result > completions_to_set(
        [
            Completion(text="DATABASE", display_meta="keyword"),
            Completion(text="TABLE", display_meta="keyword"),
            Completion(text="SYSTEM", display_meta="keyword"),
        ]
    )
    assert (
        completions_to_set([Completion(text="CREATE", display_meta="keyword")])
        not in result
    )


def test_special_name_completion(completer, complete_event):
    text = "\\"
    position = len("\\")
    result = completions_to_set(
        completer.get_completions(
            Document(text=text, cursor_position=position), complete_event
        )
    )
    # Special commands will NOT be suggested during naive completion mode.
    assert result == completions_to_set([])


def test_datatype_name_completion(completer, complete_event):
    text = "SELECT price::IN"
    position = len("SELECT price::IN")
    result = completions_to_set(
        completer.get_completions(
            Document(text=text, cursor_position=position),
            complete_event,
            smart_completion=True,
        )
    )
    assert result == completions_to_set(
        [
            Completion(text="INET", display_meta="datatype"),
            Completion(text="INT", display_meta="datatype"),
            Completion(text="INT2", display_meta="datatype"),
            Completion(text="INT4", display_meta="datatype"),
            Completion(text="INT8", display_meta="datatype"),
            Completion(text="INTEGER", display_meta="datatype"),
            Completion(text="INTERNAL", display_meta="datatype"),
            Completion(text="INTERVAL", display_meta="datatype"),
        ]
    )
