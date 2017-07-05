from __future__ import unicode_literals

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import set_app
from prompt_toolkit.input.vt100 import PipeInput
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyProcessor, KeyPress
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Window, Layout
from prompt_toolkit.output import DummyOutput

import pytest


class Handlers(object):
    def __init__(self):
        self.called = []

    def __getattr__(self, name):
        def func(event):
            self.called.append(name)
        return func


def set_dummy_app():
    app = Application(
        layout=Layout(Window()),
        output=DummyOutput(),
        input=PipeInput())
    set_app(app)


@pytest.fixture
def handlers():
    return Handlers()


@pytest.fixture
def bindings(handlers):
    set_dummy_app()

    bindings = KeyBindings()
    bindings.add(
        Keys.ControlX, Keys.ControlC)(handlers.controlx_controlc)
    bindings.add(Keys.ControlX)(handlers.control_x)
    bindings.add(Keys.ControlD)(handlers.control_d)
    bindings.add(
        Keys.ControlSquareClose, Keys.Any)(handlers.control_square_close_any)

    return bindings


@pytest.fixture
def processor(bindings):
    return KeyProcessor(bindings)


def test_remove_bindings(handlers):
    set_dummy_app()
    h = handlers.controlx_controlc
    h2 = handlers.controld

    # Test passing a handler to the remove() function.
    bindings = KeyBindings()
    bindings.add(Keys.ControlX, Keys.ControlC)(h)
    bindings.add(Keys.ControlD)(h2)
    assert len(bindings.bindings) == 2
    bindings.remove(h)
    assert len(bindings.bindings) == 1

    # Test passing a key sequence to the remove() function.
    bindings = KeyBindings()
    bindings.add(Keys.ControlX, Keys.ControlC)(h)
    bindings.add(Keys.ControlD)(h2)
    assert len(bindings.bindings) == 2
    bindings.remove(Keys.ControlX, Keys.ControlC)
    assert len(bindings.bindings) == 1


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
    registry = KeyBindings()
    registry.add('a', 'a')(handler)
    registry.add('b', 'b')(handler)
    processor = KeyProcessor(registry)

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
