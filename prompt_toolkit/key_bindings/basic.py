from __future__ import unicode_literals

from ..keys import Keys
from ..enums import InputMode
from ..line import ClipboardData

from .utils import create_handle_decorator


def basic_bindings(registry, cli_ref):
    line = cli_ref().line
    handle = create_handle_decorator(registry, line)

    @handle(Keys.F1)
    @handle(Keys.F2)
    @handle(Keys.F3)
    @handle(Keys.F4)
    @handle(Keys.F5)
    @handle(Keys.F6)
    @handle(Keys.F7)
    @handle(Keys.F8)
    @handle(Keys.F9)
    @handle(Keys.F10)
    @handle(Keys.F11)
    @handle(Keys.F12)
    @handle(Keys.F13)
    @handle(Keys.F14)
    @handle(Keys.F15)
    @handle(Keys.F16)
    @handle(Keys.F17)
    @handle(Keys.F18)
    @handle(Keys.F19)
    @handle(Keys.F20)
    @handle(Keys.ControlSpace)
    @handle(Keys.ControlBackslash)
    @handle(Keys.ControlSquareClose)
    @handle(Keys.ControlCircumflex)
    @handle(Keys.Backspace)
    @handle(Keys.Up)
    @handle(Keys.Down)
    @handle(Keys.Right)
    @handle(Keys.Left)
    @handle(Keys.Home)
    @handle(Keys.End)
    @handle(Keys.Delete)
    @handle(Keys.ShiftDelete)
    @handle(Keys.PageUp)
    @handle(Keys.PageDown)
    @handle(Keys.BackTab)
    @handle(Keys.Tab)
    def _(event):
        """
        First, for any of these keys, Don't do anything by default. Also don't
        catch them in the 'Any' handler which will insert them as data.
        """
        # We override the functionality below.
        pass

    @handle(Keys.Home)
    def _(event):
        line.cursor_position += line.document.home_position

    @handle(Keys.End)
    def _(event):
        line.cursor_position += line.document.end_position

    # CTRL keys.

    @handle(Keys.ControlA)
    def _(event):
        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=False)

    @handle(Keys.ControlB)
    def _(event):
        line.cursor_position += line.document.get_cursor_left_position(count=event.arg)

    @handle(Keys.ControlC)
    def _(event):
        line.abort()

    @handle(Keys.ControlD)
    def _(event):
        # When there is text, act as delete, otherwise call exit.
        if line.text:
            line.delete()
        else:
            line.exit()

    @handle(Keys.ControlE)
    def _(event):
        line.cursor_position += line.document.get_end_of_line_position()

    @handle(Keys.ControlF)
    def _(event):
        line.cursor_position += line.document.get_cursor_right_position(count=event.arg)

    @handle(Keys.ControlI, in_mode=InputMode.INSERT)
    @handle(Keys.ControlI, in_mode=InputMode.COMPLETE)
    def _(event):
        r"""
        Ctrl-I is identical to "\t"

        Traditional tab-completion, where the first tab completes the common
        suffix and the second tab lists all the completions.
        """
        # On the second tab-press:
        if event.second_press:
            line.list_completions()
        else:
            not line.complete_common()

    @handle(Keys.ControlJ, in_mode=InputMode.INSERT)
    @handle(Keys.ControlM, in_mode=InputMode.INSERT)
    def _(event):
        """
        Newline/Enter.
        """
        if line.is_multiline:
            line.newline()
        else:
            line.return_input()

    @handle(Keys.ControlK, in_mode=InputMode.INSERT)
    def _(event):
        deleted = line.delete(count=line.document.get_end_of_line_position())
        line.set_clipboard(ClipboardData(deleted))

    @handle(Keys.ControlL)
    def _(event):
        line.clear()

    @handle(Keys.ControlT)
    def _(event):
        line.swap_characters_before_cursor()

    @handle(Keys.ControlU, in_mode=InputMode.INSERT)
    def _(event):
        """
        Clears the line before the cursor position. If you are at the end of
        the line, clears the entire line.
        """
        deleted = line.delete_before_cursor(count=-line.document.get_start_of_line_position())
        line.set_clipboard(ClipboardData(deleted))

    @handle(Keys.ControlW, in_mode=InputMode.INSERT)
    def _(event):
        """
        Delete the word before the cursor.
        """
        pos = line.document.find_start_of_previous_word(count=event.arg)
        if pos:
            deleted = line.delete_before_cursor(count=-pos)
            line.set_clipboard(ClipboardData(deleted))

    @handle(Keys.ControlX)
    def _(event):
        pass

    @handle(Keys.ControlY, InputMode.INSERT)
    def _(event):
        # Pastes the clipboard content.
        line.paste_from_clipboard()

    @handle(Keys.PageUp, in_mode=InputMode.COMPLETE)
    def _(event):
        line.complete_previous(5)

    @handle(Keys.PageUp, in_mode=InputMode.INSERT)
    def _(event):
        line.history_backward()

    @handle(Keys.PageDown, in_mode=InputMode.COMPLETE)
    def _(event):
        line.complete_next(5)

    @handle(Keys.PageDown, in_mode=InputMode.INSERT)
    def _(event):
        line.history_forward()

    @handle(Keys.Left)
    def _(event):
        if not event.input_processor.input_mode == InputMode.INCREMENTAL_SEARCH:
            line.cursor_position += line.document.get_cursor_left_position(count=event.arg)

    @handle(Keys.Right)
    def _(event):
        if not event.input_processor.input_mode == InputMode.INCREMENTAL_SEARCH:
            line.cursor_position += line.document.get_cursor_right_position(count=event.arg)

    @handle(Keys.Up)
    def _(event):
        line.auto_up(count=event.arg)

    @handle(Keys.Down)
    def _(event):
        line.auto_down(count=event.arg)

    @handle(Keys.ControlH, in_mode=InputMode.INSERT)
    @handle(Keys.Backspace, in_mode=InputMode.INSERT)
    def _(event):
        line.delete_before_cursor(count=event.arg)

    @handle(Keys.Delete, in_mode=InputMode.INSERT)
    def _(event):
        line.delete(count=event.arg)

    @handle(Keys.ShiftDelete, in_mode=InputMode.INSERT)
    def _(event):
        line.delete(count=event.arg)

    @handle(Keys.Any, in_mode=InputMode.COMPLETE)
    @handle(Keys.Any, in_mode=InputMode.INSERT)
    def _(event):
        """
        Insert data at cursor position.
        """
        line.insert_text(event.data * event.arg)

        # Always quit autocomplete mode when the text changes.
        if event.input_processor.input_mode == InputMode.COMPLETE:
            event.input_processor.pop_input_mode()

    @handle(Keys.Escape, Keys.Left)
    def _(event):
        """
        Cursor to start of previous word.
        """
        line.cursor_position += line.document.find_previous_word_beginning(count=event.arg) or 0

    @handle(Keys.Escape, Keys.Right)
    def _(event):
        """
        Cursor to start of next word.
        """
        line.cursor_position += line.document.find_next_word_beginning(count=event.arg) or 0

    @handle(Keys.Escape, in_mode=InputMode.COMPLETE)
    @handle(Keys.ControlC, in_mode=InputMode.COMPLETE)
    def _(event):
        """
        Pressing escape or Ctrl-C in complete mode, goes back to default mode.
        """
        event.input_processor.pop_input_mode()

