"""
These are almost end-to-end tests. They create a CommandLineInterface
instance, feed it with some input and check the result.
"""
from __future__ import unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.enums import DEFAULT_BUFFER
from prompt_toolkit.eventloop.posix import PosixEventLoop
from prompt_toolkit.input import PipeInput
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.output import DummyOutput

import unittest

def _feed_cli_with_input(text):
    """
    Create a CommandLineInterface, feed it with the given user input and return
    the CLI object.

    This returns a (result, CLI) tuple.
    """
    # If the given text doesn't end with a newline, the interface won't finish.
    assert text.endswith('\n')

    loop = PosixEventLoop()
    try:
        inp = PipeInput()
        inp.send(text)
        cli = CommandLineInterface(
            application=Application(),
            eventloop=loop,
            input=inp,
            output=DummyOutput())
        result = cli.run()
        return result, cli
    finally:
        loop.close()


class FeedCliTest(unittest.TestCase):
    def test_simple_text_input(self):
        # Simple text input, followed by enter.
        result, cli = _feed_cli_with_input('hello\n')
        self.assertEqual(result.text, 'hello')
        self.assertEqual(cli.buffers[DEFAULT_BUFFER].text, 'hello')

    def test_emacs_cursor_movements(self):
        """
        Test cursor movements with Emacs key bindings.
        """
        # ControlA
        result, cli = _feed_cli_with_input('hello\x01X\n')
        self.assertEqual(result.text, 'Xhello')

        # ControlH or \b
        result, cli = _feed_cli_with_input('hello\x08X\n')
        self.assertEqual(result.text, 'hellX')

        # Left.
        result, cli = _feed_cli_with_input('hello\x1b[DX\n')
        self.assertEqual(result.text, 'hellXo')

        # ControlA, right
        result, cli = _feed_cli_with_input('hello\x01\x1b[CX\n')
        self.assertEqual(result.text, 'hXello')

        # ControlA, right
        result, cli = _feed_cli_with_input('hello\x01\x1b[CX\n')
        self.assertEqual(result.text, 'hXello')

        # ControlB (Emacs cursor left.)
        result, cli = _feed_cli_with_input('hello\x02X\n')
        self.assertEqual(result.text, 'hellXo')

        # ControlC: ignored by default, unless the prompt-bindings are loaded.
        result, cli = _feed_cli_with_input('hello\x03\n')
        self.assertEqual(result.text, 'hello')

        # ControlD: ignored by default, unless the prompt-bindings are loaded.
        result, cli = _feed_cli_with_input('hello\x04\n')
        self.assertEqual(result.text, 'hello')

        # Left, Left, ControlK
        result, cli = _feed_cli_with_input('hello\x1b[D\x1b[D\x0b\n')
        self.assertEqual(result.text, 'hel')

        # ControlL: should not influence the result.
        result, cli = _feed_cli_with_input('hello\x0c\n')
        self.assertEqual(result.text, 'hello')
