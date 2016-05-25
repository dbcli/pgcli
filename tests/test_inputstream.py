from __future__ import unicode_literals

from prompt_toolkit.terminal.vt100_input import InputStream
from prompt_toolkit.keys import Keys

import pytest


class _ProcessorMock(object):

    def __init__(self):
        self.keys = []

    def feed_key(self, key_press):
        self.keys.append(key_press)


@pytest.fixture
def processor():
    return _ProcessorMock()


@pytest.fixture
def stream(processor):
    return InputStream(processor.feed_key)


def test_control_keys(processor, stream):
    stream.feed('\x01\x02\x10')

    assert len(processor.keys) == 3
    assert processor.keys[0].key == Keys.ControlA
    assert processor.keys[1].key == Keys.ControlB
    assert processor.keys[2].key == Keys.ControlP
    assert processor.keys[0].data == '\x01'
    assert processor.keys[1].data == '\x02'
    assert processor.keys[2].data == '\x10'


def test_arrows(processor, stream):
    stream.feed('\x1b[A\x1b[B\x1b[C\x1b[D')

    assert len(processor.keys) == 4
    assert processor.keys[0].key == Keys.Up
    assert processor.keys[1].key == Keys.Down
    assert processor.keys[2].key == Keys.Right
    assert processor.keys[3].key == Keys.Left
    assert processor.keys[0].data == '\x1b[A'
    assert processor.keys[1].data == '\x1b[B'
    assert processor.keys[2].data == '\x1b[C'
    assert processor.keys[3].data == '\x1b[D'


def test_escape(processor, stream):
    stream.feed('\x1bhello')

    assert len(processor.keys) == 1 + len('hello')
    assert processor.keys[0].key == Keys.Escape
    assert processor.keys[1].key == 'h'
    assert processor.keys[0].data == '\x1b'
    assert processor.keys[1].data == 'h'


def test_special_double_keys(processor, stream):
    stream.feed('\x1b[1;3D')  # Should both send escape and left.

    assert len(processor.keys) == 2
    assert processor.keys[0].key == Keys.Escape
    assert processor.keys[1].key == Keys.Left
    assert processor.keys[0].data == '\x1b[1;3D'
    assert processor.keys[1].data == '\x1b[1;3D'


def test_flush_1(processor, stream):
    # Send left key in two parts without flush.
    stream.feed('\x1b')
    stream.feed('[D')

    assert len(processor.keys) == 1
    assert processor.keys[0].key == Keys.Left
    assert processor.keys[0].data == '\x1b[D'


def test_flush_2(processor, stream):
    # Send left key with a 'Flush' in between.
    # The flush should make sure that we process evenything before as-is,
    # with makes the first part just an escape character instead.
    stream.feed('\x1b')
    stream.flush()
    stream.feed('[D')

    assert len(processor.keys) == 3
    assert processor.keys[0].key == Keys.Escape
    assert processor.keys[1].key == '['
    assert processor.keys[2].key == 'D'

    assert processor.keys[0].data == '\x1b'
    assert processor.keys[1].data == '['
    assert processor.keys[2].data == 'D'


def test_meta_arrows(processor, stream):
    stream.feed('\x1b\x1b[D')

    assert len(processor.keys) == 2
    assert processor.keys[0].key == Keys.Escape
    assert processor.keys[1].key == Keys.Left


def test_control_square_close(processor, stream):
    stream.feed('\x1dC')

    assert len(processor.keys) == 2
    assert processor.keys[0].key == Keys.ControlSquareClose
    assert processor.keys[1].key == 'C'


def test_invalid(processor, stream):
    # Invalid sequence that has at two characters in common with other
    # sequences.
    stream.feed('\x1b[*')

    assert len(processor.keys) == 3
    assert processor.keys[0].key == Keys.Escape
    assert processor.keys[1].key == '['
    assert processor.keys[2].key == '*'


def test_cpr_response(processor, stream):
    stream.feed('a\x1b[40;10Rb')
    assert len(processor.keys) == 3
    assert processor.keys[0].key == 'a'
    assert processor.keys[1].key == Keys.CPRResponse
    assert processor.keys[2].key == 'b'


def test_cpr_response_2(processor, stream):
    # Make sure that the newline is not included in the CPR response.
    stream.feed('\x1b[40;1R\n')
    assert len(processor.keys) == 2
    assert processor.keys[0].key == Keys.CPRResponse
    assert processor.keys[1].key == Keys.ControlJ
