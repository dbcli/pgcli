# encoding: utf-8
"""
These are almost end-to-end tests. They create a CommandLineInterface
instance, feed it with some input and check the result.
"""
from __future__ import unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.eventloop.posix import PosixEventLoop
from prompt_toolkit.input import PipeInput
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.output import DummyOutput
from functools import partial

import unittest

def _feed_cli_with_input(text, editing_mode=EditingMode.EMACS):
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
        inp.send_text(text)
        cli = CommandLineInterface(
            application=Application(editing_mode=editing_mode),
            eventloop=loop,
            input=inp,
            output=DummyOutput())
        result = cli.run()
        return result, cli
    finally:
        loop.close()
        inp.close()


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

    def test_vi_cursor_movements(self):
        """
        Test cursor movements with Vi key bindings.
        """
        feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

        result, cli = feed('\x1b\n')
        self.assertEqual(result.text, '')
        self.assertEqual(cli.editing_mode, EditingMode.VI)

        # Esc h a X
        result, cli = feed('hello\x1bhaX\n')
        self.assertEqual(result.text, 'hellXo')

        # Esc I X
        result, cli = feed('hello\x1bIX\n')
        self.assertEqual(result.text, 'Xhello')

        # Esc I X
        result, cli = feed('hello\x1bIX\n')
        self.assertEqual(result.text, 'Xhello')

        # Esc 2hiX
        result, cli = feed('hello\x1b2hiX\n')
        self.assertEqual(result.text, 'heXllo')

        # Esc 2h2liX
        result, cli = feed('hello\x1b2h2liX\n')
        self.assertEqual(result.text, 'hellXo')

        # Esc \b\b
        result, cli = feed('hello\b\b\n')
        self.assertEqual(result.text, 'hel')

        # Esc \b\b
        result, cli = feed('hello\b\b\n')
        self.assertEqual(result.text, 'hel')

        # Esc 2h D
        result, cli = feed('hello\x1b2hD\n')
        self.assertEqual(result.text, 'he')

        # Esc 2h rX \n
        result, cli = feed('hello\x1b2hrX\n')
        self.assertEqual(result.text, 'heXlo')

    def test_vi_operators(self):
        feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

        # Esc g~0
        result, cli = feed('hello\x1bg~0\n')
        self.assertEqual(result.text, 'HELLo')

        # Esc gU0
        result, cli = feed('hello\x1bgU0\n')
        self.assertEqual(result.text, 'HELLo')

        # Esc d0
        result, cli = feed('hello\x1bd0\n')
        self.assertEqual(result.text, 'o')

    def test_vi_text_objects(self):
        feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

        # Esc gUgg
        result, cli = feed('hello\x1bgUgg\n')
        self.assertEqual(result.text, 'HELLO')

        # Esc di(
        result, cli = feed('before(inside)after\x1b8hdi(\n')
        self.assertEqual(result.text, 'before()after')

        # Esc di[
        result, cli = feed('before[inside]after\x1b8hdi[\n')
        self.assertEqual(result.text, 'before[]after')

        # Esc da(
        result, cli = feed('before(inside)after\x1b8hda(\n')
        self.assertEqual(result.text, 'beforeafter')

    def test_vi_digraphs(self):
        feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

        # C-K o/
        result, cli = feed('hello\x0bo/\n')
        self.assertEqual(result.text, 'helloø')

        # C-K e:
        result, cli = feed('hello\x0be:\n')
        self.assertEqual(result.text, 'helloë')
