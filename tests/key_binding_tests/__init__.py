from __future__ import unicode_literals

from prompt_toolkit.key_binding import InputProcessor, Registry
from prompt_toolkit.keys import Keys
from prompt_toolkit.inputstream import KeyPress

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
        self.registry.add_binding(Keys.ControlD)(self.handlers.controld)

        self.processor = InputProcessor(self.registry)

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
        self.assertEqual(self.handlers.called, ['controlx_controlc', 'controld'])
