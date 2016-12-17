# encoding: utf-8
"""
These are almost end-to-end tests. They create a CommandLineInterface
instance, feed it with some input and check the result.
"""
from __future__ import unicode_literals
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer, AcceptAction
from prompt_toolkit.clipboard import InMemoryClipboard, ClipboardData
from prompt_toolkit.enums import DEFAULT_BUFFER, EditingMode
from prompt_toolkit.eventloop.posix import PosixEventLoop
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.input import PipeInput
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.output import DummyOutput
from prompt_toolkit.terminal.vt100_input import ANSI_SEQUENCES
from functools import partial
import pytest


def _history():
    h = InMemoryHistory()
    h.append('line1 first input')
    h.append('line2 second input')
    h.append('line3 third input')
    return h


def _feed_cli_with_input(text, editing_mode=EditingMode.EMACS, clipboard=None,
                         history=None, multiline=False, check_line_ending=True,
                         pre_run_callback=None):
    """
    Create a CommandLineInterface, feed it with the given user input and return
    the CLI object.

    This returns a (result, CLI) tuple.
    """
    # If the given text doesn't end with a newline, the interface won't finish.
    if check_line_ending:
        assert text.endswith('\n')

    loop = PosixEventLoop()
    try:
        inp = PipeInput()
        inp.send_text(text)
        cli = CommandLineInterface(
            application=Application(
                buffer=Buffer(accept_action=AcceptAction.RETURN_DOCUMENT,
                              history=history, is_multiline=multiline),
                editing_mode=editing_mode,
                clipboard=clipboard or InMemoryClipboard(),
                key_bindings_registry=KeyBindingManager.for_prompt().registry,
            ),
            eventloop=loop,
            input=inp,
            output=DummyOutput())

        if pre_run_callback:
            pre_run_callback(cli)

        result = cli.run()
        return result, cli
    finally:
        loop.close()
        inp.close()


def test_simple_text_input():
    # Simple text input, followed by enter.
    result, cli = _feed_cli_with_input('hello\n')
    assert result.text == 'hello'
    assert cli.buffers[DEFAULT_BUFFER].text == 'hello'


def test_emacs_cursor_movements():
    """
    Test cursor movements with Emacs key bindings.
    """
    # ControlA (beginning-of-line)
    result, cli = _feed_cli_with_input('hello\x01X\n')
    assert result.text == 'Xhello'

    # ControlE (end-of-line)
    result, cli = _feed_cli_with_input('hello\x01X\x05Y\n')
    assert result.text == 'XhelloY'

    # ControlH or \b
    result, cli = _feed_cli_with_input('hello\x08X\n')
    assert result.text == 'hellX'

    # Delete.  (Left, left, delete)
    result, cli = _feed_cli_with_input('hello\x1b[D\x1b[D\x1b[3~\n')
    assert result.text == 'helo'

    # Left.
    result, cli = _feed_cli_with_input('hello\x1b[DX\n')
    assert result.text == 'hellXo'

    # ControlA, right
    result, cli = _feed_cli_with_input('hello\x01\x1b[CX\n')
    assert result.text == 'hXello'

    # ControlA, right
    result, cli = _feed_cli_with_input('hello\x01\x1b[CX\n')
    assert result.text == 'hXello'

    # ControlB (backward-char)
    result, cli = _feed_cli_with_input('hello\x02X\n')
    assert result.text == 'hellXo'

    # ControlF (forward-char)
    result, cli = _feed_cli_with_input('hello\x01\x06X\n')
    assert result.text == 'hXello'

    # ControlC: raise KeyboardInterrupt.
    with pytest.raises(KeyboardInterrupt):
        result, cli = _feed_cli_with_input('hello\x03\n')
        assert result.text == 'hello'

    # ControlD without any input: raises EOFError.
    with pytest.raises(EOFError):
        result, cli = _feed_cli_with_input('\x04\n')
        assert result.text == 'hello'

    # ControlD: delete after cursor.
    result, cli = _feed_cli_with_input('hello\x01\x04\n')
    assert result.text == 'ello'

    # ControlD at the end of the input ssshould not do anything.
    result, cli = _feed_cli_with_input('hello\x04\n')
    assert result.text == 'hello'

    # Left, Left, ControlK  (kill-line)
    result, cli = _feed_cli_with_input('hello\x1b[D\x1b[D\x0b\n')
    assert result.text == 'hel'

    # Left, Left Esc- ControlK (kill-line, but negative)
    result, cli = _feed_cli_with_input('hello\x1b[D\x1b[D\x1b-\x0b\n')
    assert result.text == 'lo'

    # ControlL: should not influence the result.
    result, cli = _feed_cli_with_input('hello\x0c\n')
    assert result.text == 'hello'

    # ControlRight (forward-word)
    result, cli = _feed_cli_with_input('hello world\x01X\x1b[1;5CY\n')
    assert result.text == 'XhelloY world'

    # ContrlolLeft (backward-word)
    result, cli = _feed_cli_with_input('hello world\x1b[1;5DY\n')
    assert result.text == 'hello Yworld'

    # <esc>-f with argument. (forward-word)
    result, cli = _feed_cli_with_input('hello world abc def\x01\x1b3\x1bfX\n')
    assert result.text == 'hello world abcX def'

    # <esc>-f with negative argument. (forward-word)
    result, cli = _feed_cli_with_input('hello world abc def\x1b-\x1b3\x1bfX\n')
    assert result.text == 'hello Xworld abc def'

    # <esc>-b with argument. (backward-word)
    result, cli = _feed_cli_with_input('hello world abc def\x1b3\x1bbX\n')
    assert result.text == 'hello Xworld abc def'

    # <esc>-b with negative argument. (backward-word)
    result, cli = _feed_cli_with_input('hello world abc def\x01\x1b-\x1b3\x1bbX\n')
    assert result.text == 'hello world abc Xdef'

    # ControlW (kill-word / unix-word-rubout)
    result, cli = _feed_cli_with_input('hello world\x17\n')
    assert result.text == 'hello '
    assert cli.clipboard.get_data().text == 'world'

    result, cli = _feed_cli_with_input('test hello world\x1b2\x17\n')
    assert result.text == 'test '

    # Escape Backspace (unix-word-rubout)
    result, cli = _feed_cli_with_input('hello world\x1b\x7f\n')
    assert result.text == 'hello '
    assert cli.clipboard.get_data().text == 'world'

    result, cli = _feed_cli_with_input('hello world\x1b\x08\n')
    assert result.text == 'hello '
    assert cli.clipboard.get_data().text == 'world'

    # Backspace (backward-delete-char)
    result, cli = _feed_cli_with_input('hello world\x7f\n')
    assert result.text == 'hello worl'
    assert result.cursor_position == len('hello worl')

    result, cli = _feed_cli_with_input('hello world\x08\n')
    assert result.text == 'hello worl'
    assert result.cursor_position == len('hello worl')

    # Delete (delete-char)
    result, cli = _feed_cli_with_input('hello world\x01\x1b[3~\n')
    assert result.text == 'ello world'
    assert result.cursor_position == 0

    # Escape-\\ (delete-horizontal-space)
    result, cli = _feed_cli_with_input('hello     world\x1b8\x02\x1b\\\n')
    assert result.text == 'helloworld'
    assert result.cursor_position == len('hello')


def test_emacs_yank():
    # ControlY (yank)
    c = InMemoryClipboard(ClipboardData('XYZ'))
    result, cli = _feed_cli_with_input('hello\x02\x19\n', clipboard=c)
    assert result.text == 'hellXYZo'
    assert result.cursor_position == len('hellXYZ')


def test_quoted_insert():
    # ControlQ - ControlB (quoted-insert)
    result, cli = _feed_cli_with_input('hello\x11\x02\n')
    assert result.text == 'hello\x02'


def test_transformations():
    # Meta-c (capitalize-word)
    result, cli = _feed_cli_with_input('hello world\01\x1bc\n')
    assert result.text == 'Hello world'
    assert result.cursor_position == len('Hello')

    # Meta-u (uppercase-word)
    result, cli = _feed_cli_with_input('hello world\01\x1bu\n')
    assert result.text == 'HELLO world'
    assert result.cursor_position == len('Hello')

    # Meta-u (downcase-word)
    result, cli = _feed_cli_with_input('HELLO WORLD\01\x1bl\n')
    assert result.text == 'hello WORLD'
    assert result.cursor_position == len('Hello')

    # ControlT (transpose-chars)
    result, cli = _feed_cli_with_input('hello\x14\n')
    assert result.text == 'helol'
    assert result.cursor_position == len('hello')

    # Left, Left, Control-T (transpose-chars)
    result, cli = _feed_cli_with_input('abcde\x1b[D\x1b[D\x14\n')
    assert result.text == 'abdce'
    assert result.cursor_position == len('abcd')


def test_emacs_other_bindings():
    # Transpose characters.
    result, cli = _feed_cli_with_input('abcde\x14X\n')  # Ctrl-T
    assert result.text == 'abcedX'

    # Left, Left, Transpose. (This is slightly different.)
    result, cli = _feed_cli_with_input('abcde\x1b[D\x1b[D\x14X\n')
    assert result.text == 'abdcXe'

    # Clear before cursor.
    result, cli = _feed_cli_with_input('hello\x1b[D\x1b[D\x15X\n')
    assert result.text == 'Xlo'

    # unix-word-rubout: delete word before the cursor.
    # (ControlW).
    result, cli = _feed_cli_with_input('hello world test\x17X\n')
    assert result.text == 'hello world X'

    result, cli = _feed_cli_with_input('hello world /some/very/long/path\x17X\n')
    assert result.text == 'hello world X'

    # (with argument.)
    result, cli = _feed_cli_with_input('hello world test\x1b2\x17X\n')
    assert result.text == 'hello X'

    result, cli = _feed_cli_with_input('hello world /some/very/long/path\x1b2\x17X\n')
    assert result.text == 'hello X'

    # backward-kill-word: delete word before the cursor.
    # (Esc-ControlH).
    result, cli = _feed_cli_with_input('hello world /some/very/long/path\x1b\x08X\n')
    assert result.text == 'hello world /some/very/long/X'

    # (with arguments.)
    result, cli = _feed_cli_with_input('hello world /some/very/long/path\x1b3\x1b\x08X\n')
    assert result.text == 'hello world /some/very/X'


def test_controlx_controlx():
    # At the end: go to the start of the line.
    result, cli = _feed_cli_with_input('hello world\x18\x18X\n')
    assert result.text == 'Xhello world'
    assert result.cursor_position == 1

    # At the start: go to the end of the line.
    result, cli = _feed_cli_with_input('hello world\x01\x18\x18X\n')
    assert result.text == 'hello worldX'

    # Left, Left Control-X Control-X: go to the end of the line.
    result, cli = _feed_cli_with_input('hello world\x1b[D\x1b[D\x18\x18X\n')
    assert result.text == 'hello worldX'


def test_emacs_history_bindings():
    # Adding a new item to the history.
    history = _history()
    result, cli = _feed_cli_with_input('new input\n', history=history)
    assert result.text == 'new input'
    history.strings[-1] == 'new input'

    # Go up in history, and accept the last item.
    result, cli = _feed_cli_with_input('hello\x1b[A\n', history=history)
    assert result.text == 'new input'

    # Esc< (beginning-of-history)
    result, cli = _feed_cli_with_input('hello\x1b<\n', history=history)
    assert result.text == 'line1 first input'

    # Esc> (end-of-history)
    result, cli = _feed_cli_with_input('another item\x1b[A\x1b[a\x1b>\n', history=history)
    assert result.text == 'another item'

    # ControlUp (previous-history)
    result, cli = _feed_cli_with_input('\x1b[1;5A\n', history=history)
    assert result.text == 'another item'

    # Esc< ControlDown (beginning-of-history, next-history)
    result, cli = _feed_cli_with_input('\x1b<\x1b[1;5B\n', history=history)
    assert result.text == 'line2 second input'


def test_emacs_reverse_search():
    history = _history()

    # ControlR  (reverse-search-history)
    result, cli = _feed_cli_with_input('\x12input\n\n', history=history)
    assert result.text == 'line3 third input'

    # Hitting ControlR twice.
    result, cli = _feed_cli_with_input('\x12input\x12\n\n', history=history)
    assert result.text == 'line2 second input'


def test_emacs_arguments():
    """
    Test various combinations of arguments in Emacs mode.
    """
    # esc 4
    result, cli = _feed_cli_with_input('\x1b4x\n')
    assert result.text == 'xxxx'

    # esc 4 4
    result, cli = _feed_cli_with_input('\x1b44x\n')
    assert result.text == 'x' * 44

    # esc 4 esc 4
    result, cli = _feed_cli_with_input('\x1b4\x1b4x\n')
    assert result.text == 'x' * 44

    # esc - right (-1 position to the right, equals 1 to the left.)
    result, cli = _feed_cli_with_input('aaaa\x1b-\x1b[Cbbbb\n')
    assert result.text == 'aaabbbba'

    # esc - 3 right
    result, cli = _feed_cli_with_input('aaaa\x1b-3\x1b[Cbbbb\n')
    assert result.text == 'abbbbaaa'

    # esc - - - 3 right
    result, cli = _feed_cli_with_input('aaaa\x1b---3\x1b[Cbbbb\n')
    assert result.text == 'abbbbaaa'


def test_emacs_arguments_for_all_commands():
    """
    Test all Emacs commands with Meta-[0-9] arguments (both positive and
    negative). No one should crash.
    """
    for key in ANSI_SEQUENCES:
        # Ignore BracketedPaste. This would hang forever, because it waits for
        # the end sequence.
        if key != '\x1b[200~':
            try:
                # Note: we add an 'X' after the key, because Ctrl-Q (quoted-insert)
                # expects something to follow. We add an additional \n, because
                # Ctrl-R and Ctrl-S (reverse-search) expect that.
                result, cli = _feed_cli_with_input(
                    'hello\x1b4' + key + 'X\n\n')

                result, cli = _feed_cli_with_input(
                    'hello\x1b-' + key + 'X\n\n')
            except KeyboardInterrupt:
                # This exception should only be raised for Ctrl-C
                assert key == '\x03'


def test_emacs_kill_ring():
    operations = (
        # abc ControlA ControlK
        'abc\x01\x0b'

        # def ControlA ControlK
        'def\x01\x0b'

        # ghi ControlA ControlK
        'ghi\x01\x0b'

        # ControlY (yank)
        '\x19'
    )

    result, cli = _feed_cli_with_input(operations + '\n')
    assert result.text == 'ghi'

    result, cli = _feed_cli_with_input(operations + '\x1by\n')
    assert result.text == 'def'

    result, cli = _feed_cli_with_input(operations + '\x1by\x1by\n')
    assert result.text == 'abc'

    result, cli = _feed_cli_with_input(operations + '\x1by\x1by\x1by\n')
    assert result.text == 'ghi'


def test_emacs_insert_comment():
    # Test insert-comment (M-#) binding.
    result, cli = _feed_cli_with_input('hello\x1b#', check_line_ending=False)
    assert result.text == '#hello'

    result, cli = _feed_cli_with_input(
        'hello\nworld\x1b#', check_line_ending=False, multiline=True)
    assert result.text == '#hello\n#world'


def test_emacs_record_macro():
    operations = (
        '  '
        '\x18('  # Start recording macro. C-X(
        'hello'
        '\x18)'  # Stop recording macro.
        '  '
        '\x18e'  # Execute macro.
        '\x18e'  # Execute macro.
        '\n'
    )

    result, cli = _feed_cli_with_input(operations)
    assert result.text == '  hello  hellohello'


def test_prefix_meta():
    # Test the prefix-meta command.
    def setup_keybindings(cli):
        from prompt_toolkit.key_binding.bindings.named_commands import prefix_meta
        from prompt_toolkit.filters import ViInsertMode
        cli.application.key_bindings_registry.add_binding('j', 'j', filter=ViInsertMode())(prefix_meta)

    result, cli = _feed_cli_with_input(
        'hellojjIX\n', pre_run_callback=setup_keybindings, editing_mode=EditingMode.VI)
    assert result.text == 'Xhello'


def test_bracketed_paste():
    result, cli = _feed_cli_with_input('\x1b[200~hello world\x1b[201~\n')
    assert result.text == 'hello world'

    result, cli = _feed_cli_with_input('\x1b[200~hello\nworld\x1b[201~\x1b\n')
    assert result.text == 'hello\nworld'

    # With \r\n endings.
    result, cli = _feed_cli_with_input('\x1b[200~hello\r\nworld\x1b[201~\x1b\n')
    assert result.text == 'hello\nworld'

    # With \r endings.
    result, cli = _feed_cli_with_input('\x1b[200~hello\rworld\x1b[201~\x1b\n')
    assert result.text == 'hello\nworld'


def test_vi_cursor_movements():
    """
    Test cursor movements with Vi key bindings.
    """
    feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

    result, cli = feed('\x1b\n')
    assert result.text == ''
    assert cli.editing_mode == EditingMode.VI

    # Esc h a X
    result, cli = feed('hello\x1bhaX\n')
    assert result.text == 'hellXo'

    # Esc I X
    result, cli = feed('hello\x1bIX\n')
    assert result.text == 'Xhello'

    # Esc I X
    result, cli = feed('hello\x1bIX\n')
    assert result.text == 'Xhello'

    # Esc 2hiX
    result, cli = feed('hello\x1b2hiX\n')
    assert result.text == 'heXllo'

    # Esc 2h2liX
    result, cli = feed('hello\x1b2h2liX\n')
    assert result.text == 'hellXo'

    # Esc \b\b
    result, cli = feed('hello\b\b\n')
    assert result.text == 'hel'

    # Esc \b\b
    result, cli = feed('hello\b\b\n')
    assert result.text == 'hel'

    # Esc 2h D
    result, cli = feed('hello\x1b2hD\n')
    assert result.text == 'he'

    # Esc 2h rX \n
    result, cli = feed('hello\x1b2hrX\n')
    assert result.text == 'heXlo'


def test_vi_operators():
    feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

    # Esc g~0
    result, cli = feed('hello\x1bg~0\n')
    assert result.text == 'HELLo'

    # Esc gU0
    result, cli = feed('hello\x1bgU0\n')
    assert result.text == 'HELLo'

    # Esc d0
    result, cli = feed('hello\x1bd0\n')
    assert result.text == 'o'


def test_vi_text_objects():
    feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

    # Esc gUgg
    result, cli = feed('hello\x1bgUgg\n')
    assert result.text == 'HELLO'

    # Esc gUU
    result, cli = feed('hello\x1bgUU\n')
    assert result.text == 'HELLO'

    # Esc di(
    result, cli = feed('before(inside)after\x1b8hdi(\n')
    assert result.text == 'before()after'

    # Esc di[
    result, cli = feed('before[inside]after\x1b8hdi[\n')
    assert result.text == 'before[]after'

    # Esc da(
    result, cli = feed('before(inside)after\x1b8hda(\n')
    assert result.text == 'beforeafter'


def test_vi_digraphs():
    feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

    # C-K o/
    result, cli = feed('hello\x0bo/\n')
    assert result.text == 'helloø'

    # C-K /o  (reversed input.)
    result, cli = feed('hello\x0b/o\n')
    assert result.text == 'helloø'

    # C-K e:
    result, cli = feed('hello\x0be:\n')
    assert result.text == 'helloë'

    # C-K xxy (Unknown digraph.)
    result, cli = feed('hello\x0bxxy\n')
    assert result.text == 'helloy'


def test_vi_block_editing():
    " Test Vi Control-V style block insertion. "
    feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI,
                   multiline=True)

    operations = (
        # Three lines of text.
        '-line1\n-line2\n-line3\n-line4\n-line5\n-line6'
        # Go to the second character of the second line.
        '\x1bkkkkkkkj0l'
        # Enter Visual block mode.
        '\x16'
        # Go down two more lines.
        'jj'
        # Go 3 characters to the right.
        'lll'
        # Go to insert mode.
        'insert'  # (Will be replaced.)
        # Insert stars.
        '***'
        # Escape again.
        '\x1b\n')

    # Control-I
    result, cli = feed(operations.replace('insert', 'I'))

    assert (result.text ==
            '-line1\n-***line2\n-***line3\n-***line4\n-line5\n-line6')

    # Control-A
    result, cli = feed(operations.replace('insert', 'A'))

    assert (result.text ==
            '-line1\n-line***2\n-line***3\n-line***4\n-line5\n-line6')


def test_vi_character_paste():
    feed = partial(_feed_cli_with_input, editing_mode=EditingMode.VI)

    # Test 'p' character paste.
    result, cli = feed('abcde\x1bhhxp\n')
    assert result.text == 'abdce'
    assert result.cursor_position == 3

    # Test 'P' character paste.
    result, cli = feed('abcde\x1bhhxP\n')
    assert result.text == 'abcde'
    assert result.cursor_position == 2
