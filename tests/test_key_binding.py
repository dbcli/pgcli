from __future__ import unicode_literals

from prompt_toolkit.key_binding.input_processor import InputProcessor, KeyPress
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.keys import Keys

import pytest


class Handlers(object):

    def __init__(self):
        self.called = []

    def __getattr__(self, name):
        def func(event):
            self.called.append(name)
        return func


@pytest.fixture
def handlers():
    return Handlers()


@pytest.fixture
def registry(handlers):
    registry = Registry()
    registry.add_binding(
        Keys.ControlX, Keys.ControlC)(handlers.controlx_controlc)
    registry.add_binding(Keys.ControlX)(handlers.control_x)
    registry.add_binding(Keys.ControlD)(handlers.control_d)
    registry.add_binding(
        Keys.ControlSquareClose, Keys.Any)(handlers.control_square_close_any)

    return registry


@pytest.fixture
def processor(registry):
    return InputProcessor(registry, lambda: None)


def test_feed_simple(processor, handlers):
    processor.feed(KeyPress(Keys.ControlX, '\x18'))
    processor.feed(KeyPress(Keys.ControlC, '\x03'))
    processor.process_keys()

    assert handlers.called == ['controlx_controlc']


def test_feed_several(processor, handlers):
    # First an unknown key first.
    processor.feed(KeyPress(Keys.ControlQ, ''))
    processor.process_keys()

    assert handlers.called == []

    # Followed by a know key sequence.
    processor.feed(KeyPress(Keys.ControlX, ''))
    processor.feed(KeyPress(Keys.ControlC, ''))
    processor.process_keys()

    assert handlers.called == ['controlx_controlc']

    # Followed by another unknown sequence.
    processor.feed(KeyPress(Keys.ControlR, ''))
    processor.feed(KeyPress(Keys.ControlS, ''))

    # Followed again by a know key sequence.
    processor.feed(KeyPress(Keys.ControlD, ''))
    processor.process_keys()

    assert handlers.called == ['controlx_controlc', 'control_d']


def test_control_square_closed_any(processor, handlers):
    processor.feed(KeyPress(Keys.ControlSquareClose, ''))
    processor.feed(KeyPress('C', 'C'))
    processor.process_keys()

    assert handlers.called == ['control_square_close_any']


def test_common_prefix(processor, handlers):
    # Sending Control_X should not yet do anything, because there is
    # another sequence starting with that as well.
    processor.feed(KeyPress(Keys.ControlX, ''))
    processor.process_keys()

    assert handlers.called == []

    # When another key is pressed, we know that we did not meant the longer
    # "ControlX ControlC" sequence and the callbacks are called.
    processor.feed(KeyPress(Keys.ControlD, ''))
    processor.process_keys()

    assert handlers.called == ['control_x', 'control_d']


def test_previous_key_sequence(processor, handlers):
    """
    test whether we receive the correct previous_key_sequence.
    """
    events = []
    def handler(event):
        events.append(event)

    # Build registry.
    registry = Registry()
    registry.add_binding('a', 'a')(handler)
    registry.add_binding('b', 'b')(handler)
    processor = InputProcessor(registry, lambda: None)

    # Create processor and feed keys.
    processor.feed(KeyPress('a', 'a'))
    processor.feed(KeyPress('a', 'a'))
    processor.feed(KeyPress('b', 'b'))
    processor.feed(KeyPress('b', 'b'))
    processor.process_keys()

    # Test.
    assert len(events) == 2
    assert len(events[0].key_sequence) == 2
    assert events[0].key_sequence[0].key == 'a'
    assert events[0].key_sequence[0].data == 'a'
    assert events[0].key_sequence[1].key == 'a'
    assert events[0].key_sequence[1].data == 'a'
    assert events[0].previous_key_sequence == []

    assert len(events[1].key_sequence) == 2
    assert events[1].key_sequence[0].key == 'b'
    assert events[1].key_sequence[0].data == 'b'
    assert events[1].key_sequence[1].key == 'b'
    assert events[1].key_sequence[1].data == 'b'
    assert len(events[1].previous_key_sequence) == 2
    assert events[1].previous_key_sequence[0].key == 'a'
    assert events[1].previous_key_sequence[0].data == 'a'
    assert events[1].previous_key_sequence[1].key == 'a'
    assert events[1].previous_key_sequence[1].data == 'a'
