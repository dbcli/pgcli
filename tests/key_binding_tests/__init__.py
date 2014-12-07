from __future__ import unicode_literals

from prompt_toolkit.key_binding.input_processor import InputProcessor, KeyPress
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.keys import Keys

import unittest


class KeyBindingTest(unittest.TestCase):
    def setUp(self):
        class Handlers(object):
            def __init__(self):
                self.called = []

            def __getattr__(self, name):
                def func(event):
                    self.called.append(name)
                return func

        self.handlers = Handlers()

        self.registry = Registry()
        self.registry.add_binding(Keys.ControlX, Keys.ControlC)(self.handlers.controlx_controlc)
        self.registry.add_binding(Keys.ControlX)(self.handlers.control_x)
        self.registry.add_binding(Keys.ControlD)(self.handlers.control_d)
        self.registry.add_binding(Keys.ControlSquareClose, Keys.Any)(self.handlers.control_square_close_any)

        self.processor = InputProcessor(self.registry, lambda: None)

    def test_feed_simple(self):
        self.processor.feed_key(KeyPress(Keys.ControlX, '\x18'))
        self.processor.feed_key(KeyPress(Keys.ControlC, '\x03'))

        self.assertEqual(self.handlers.called, ['controlx_controlc'])

    def test_feed_several(self):
        # First an unknown key first.
        self.processor.feed_key(KeyPress(Keys.ControlQ, ''))
        self.assertEqual(self.handlers.called, [])

        # Followed by a know key sequence.
        self.processor.feed_key(KeyPress(Keys.ControlX, ''))
        self.processor.feed_key(KeyPress(Keys.ControlC, ''))
        self.assertEqual(self.handlers.called, ['controlx_controlc'])

        # Followed by another unknown sequence.
        self.processor.feed_key(KeyPress(Keys.ControlR, ''))
        self.processor.feed_key(KeyPress(Keys.ControlS, ''))

        # Followed again by a know key sequence.
        self.processor.feed_key(KeyPress(Keys.ControlD, ''))
        self.assertEqual(self.handlers.called, ['controlx_controlc', 'control_d'])

    def test_control_square_closed_any(self):
        self.processor.feed_key(KeyPress(Keys.ControlSquareClose, ''))
        self.processor.feed_key(KeyPress('C', 'C'))

        self.assertEqual(self.handlers.called, ['control_square_close_any'])

    def test_common_prefix(self):
        # Sending Control_X should not yet do anything, because there is
        # another sequence starting with that as well.
        self.processor.feed_key(KeyPress(Keys.ControlX, ''))
        self.assertEqual(self.handlers.called, [])

        # When another key is pressed, we know that we did not meant the longer
        # "ControlX ControlC" sequence and the callbacks are called.
        self.processor.feed_key(KeyPress(Keys.ControlD, ''))

        self.assertEqual(self.handlers.called, ['control_x', 'control_d'])
