from __future__ import unicode_literals

import pytest

from prompt_toolkit.document import Document


@pytest.fixture
def document():
    return Document(
        'line 1\n' +
        'line 2\n' +
        'line 3\n' +
        'line 4\n',
        len('line 1\n' + 'lin')
    )


def test_current_char(document):
    assert document.current_char == 'e'


def test_text_before_cursor(document):
    assert document.text_before_cursor == 'line 1\nlin'


def test_text_after_cursor(document):
    assert document.text_after_cursor == 'e 2\n' + \
        'line 3\n' + \
        'line 4\n'


def test_lines(document):
    assert document.lines == [
        'line 1',
        'line 2',
        'line 3',
        'line 4', '']


def test_line_count(document):
    assert document.line_count == 5


def test_current_line_before_cursor(document):
    assert document.current_line_before_cursor == 'lin'


def test_current_line_after_cursor(document):
    assert document.current_line_after_cursor == 'e 2'


def test_current_line(document):
    assert document.current_line == 'line 2'


def test_cursor_position(document):
    assert document.cursor_position_row == 1
    assert document.cursor_position_col == 3

    d = Document('', 0)
    assert d.cursor_position_row == 0
    assert d.cursor_position_col == 0


def test_translate_index_to_position(document):
    pos = document.translate_index_to_position(
        len('line 1\nline 2\nlin'))

    assert pos[0] == 2
    assert pos[1] == 3

    pos = document.translate_index_to_position(0)
    assert pos == (0, 0)
