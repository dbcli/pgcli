from __future__ import unicode_literals
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.eventloop.defaults import create_event_loop

import pytest


@pytest.fixture
def _history():
    " Prefilled history. "
    history = InMemoryHistory()
    history.append('alpha beta gamma delta')
    history.append('one two three four')
    return history


@pytest.fixture
def _loop():
    loop = create_event_loop()
    yield loop
    loop.close()

# Test yank_last_arg.


def test_empty_history(_loop):
    buf = Buffer(loop=_loop)
    buf.yank_last_arg()
    assert buf.document.current_line == ''


def test_simple_search(_history, _loop):
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_last_arg()
    assert buff.document.current_line == 'four'


def test_simple_search_with_quotes(_history, _loop):
    _history.append("""one two "three 'x' four"\n""")
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_last_arg()
    assert buff.document.current_line == '''"three 'x' four"'''


def test_simple_search_with_arg(_history, _loop):
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_last_arg(n=2)
    assert buff.document.current_line == 'three'


def test_simple_search_with_arg_out_of_bounds(_history, _loop):
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_last_arg(n=8)
    assert buff.document.current_line == ''


def test_repeated_search(_history, _loop):
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_last_arg()
    buff.yank_last_arg()
    assert buff.document.current_line == 'delta'


def test_repeated_search_with_wraparound(_history, _loop):
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_last_arg()
    buff.yank_last_arg()
    buff.yank_last_arg()
    assert buff.document.current_line == 'four'


# Test yank_last_arg.


def test_yank_nth_arg(_history, _loop):
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_nth_arg()
    assert buff.document.current_line == 'two'


def test_repeated_yank_nth_arg(_history, _loop):
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_nth_arg()
    buff.yank_nth_arg()
    assert buff.document.current_line == 'beta'


def test_yank_nth_arg_with_arg(_history, _loop):
    buff = Buffer(history=_history, loop=_loop)
    buff.yank_nth_arg(n=2)
    assert buff.document.current_line == 'three'
