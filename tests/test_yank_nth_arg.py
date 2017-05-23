from __future__ import unicode_literals
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.history import InMemoryHistory

import pytest


@pytest.fixture
def _history():
    " Prefilled history. "
    history = InMemoryHistory()
    history.append('alpha beta gamma delta')
    history.append('one two three four')
    return history


# Test yank_last_arg.


def test_empty_history():
    buf = Buffer()
    buf.yank_last_arg()
    assert buf.document.current_line == ''


def test_simple_search(_history):
    buff = Buffer(history=_history)
    buff.yank_last_arg()
    assert buff.document.current_line == 'four'


def test_simple_search_with_quotes(_history):
    _history.append("""one two "three 'x' four"\n""")
    buff = Buffer(history=_history)
    buff.yank_last_arg()
    assert buff.document.current_line == '''"three 'x' four"'''


def test_simple_search_with_arg(_history):
    buff = Buffer(history=_history)
    buff.yank_last_arg(n=2)
    assert buff.document.current_line == 'three'


def test_simple_search_with_arg_out_of_bounds(_history):
    buff = Buffer(history=_history)
    buff.yank_last_arg(n=8)
    assert buff.document.current_line == ''


def test_repeated_search(_history):
    buff = Buffer(history=_history)
    buff.yank_last_arg()
    buff.yank_last_arg()
    assert buff.document.current_line == 'delta'


def test_repeated_search_with_wraparound(_history):
    buff = Buffer(history=_history)
    buff.yank_last_arg()
    buff.yank_last_arg()
    buff.yank_last_arg()
    assert buff.document.current_line == 'four'


# Test yank_last_arg.


def test_yank_nth_arg(_history):
    buff = Buffer(history=_history)
    buff.yank_nth_arg()
    assert buff.document.current_line == 'two'


def test_repeated_yank_nth_arg(_history):
    buff = Buffer(history=_history)
    buff.yank_nth_arg()
    buff.yank_nth_arg()
    assert buff.document.current_line == 'beta'


def test_yank_nth_arg_with_arg(_history):
    buff = Buffer(history=_history)
    buff.yank_nth_arg(n=2)
    assert buff.document.current_line == 'three'
