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

    @handle(Keys.Home, in_mode=InputMode.INSERT)
    @handle(Keys.Home, in_mode=InputMode.SELECTION)
    def _(event):
        line.cursor_position += line.document.home_position

    @handle(Keys.End, in_mode=InputMode.INSERT)
    @handle(Keys.End, in_mode=InputMode.SELECTION)
    def _(event):
        line.cursor_position += line.document.end_position

    # CTRL keys.

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

    @handle(Keys.ControlI, in_mode=InputMode.INSERT)
    @handle(Keys.ControlI, in_mode=InputMode.COMPLETE)
    def _(event):
        r"""
        Ctrl-I is identical to "\t"

        Traditional tab-completion, where the first tab completes the common
        suffix and the second tab lists all the completions.
        """
        def second_tab():
            line.complete_next(start_at_first=False)

            # Go to completion mode. (If we're not there yet.)
            if event.input_processor.input_mode != InputMode.COMPLETE:
                event.input_processor.push_input_mode(InputMode.COMPLETE)

        # On the second tab-press:
        if event.second_press or event.input_processor.input_mode == InputMode.COMPLETE:
            second_tab()
        else:
            # On the first tab press, only complete the common parts of all completions.
            has_common = line.complete_common()
            if not has_common:
                second_tab()

    @handle(Keys.BackTab, in_mode=InputMode.COMPLETE)
    def _(event):
        """
        Shift+Tab: go to previous completion.
        """
        line.complete_previous()

    @handle(Keys.ControlJ, in_mode=InputMode.INSERT)
    @handle(Keys.ControlM, in_mode=InputMode.INSERT)
    @handle(Keys.ControlJ, in_mode=InputMode.COMPLETE)
    @handle(Keys.ControlM, in_mode=InputMode.COMPLETE)
    def _(event):
        """
        Newline/Enter. (Or return input.)
        """
        line.auto_enter()

    @handle(Keys.ControlK, in_mode=InputMode.INSERT)
    def _(event):
        deleted = line.delete(count=line.document.get_end_of_line_position())
        line.set_clipboard(ClipboardData(deleted))

    @handle(Keys.ControlL)
    def _(event):
        line.clear()

    @handle(Keys.ControlT, in_mode=InputMode.INSERT)
    def _(event):
        line.swap_characters_before_cursor()

    @handle(Keys.ControlU, in_mode=InputMode.INSERT)
    @handle(Keys.ControlU, in_mode=InputMode.COMPLETE)
    def _(event):
        """
        Clears the line before the cursor position. If you are at the end of
        the line, clears the entire line.
        """
        deleted = line.delete_before_cursor(count=-line.document.get_start_of_line_position())
        line.set_clipboard(ClipboardData(deleted))

        # Quit autocomplete mode.
        if event.input_processor.input_mode == InputMode.COMPLETE:
            event.input_processor.pop_input_mode()

    @handle(Keys.ControlW, in_mode=InputMode.INSERT)
    @handle(Keys.ControlW, in_mode=InputMode.COMPLETE)
    def _(event):
        """
        Delete the word before the cursor.
        """
        pos = line.document.find_start_of_previous_word(count=event.arg)
        if pos:
            deleted = line.delete_before_cursor(count=-pos)
            line.set_clipboard(ClipboardData(deleted))

        # Quit autocomplete mode.
        if event.input_processor.input_mode == InputMode.COMPLETE:
            event.input_processor.pop_input_mode()

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

    @handle(Keys.Left, in_mode=InputMode.INSERT)
    @handle(Keys.Left, in_mode=InputMode.SELECTION)
    def _(event):
        line.cursor_position += line.document.get_cursor_left_position(count=event.arg)

    @handle(Keys.Right, in_mode=InputMode.INSERT)
    @handle(Keys.Right, in_mode=InputMode.SELECTION)
    def _(event):
        line.cursor_position += line.document.get_cursor_right_position(count=event.arg)

    @handle(Keys.Up, in_mode=InputMode.INSERT)
    def _(event):
        line.auto_up(count=event.arg)

    @handle(Keys.Down, in_mode=InputMode.INSERT)
    def _(event):
        line.auto_down(count=event.arg)

    @handle(Keys.Up, in_mode=InputMode.SELECTION)
    def _(event):
        line.cursor_up(count=event.arg)

    @handle(Keys.Down, in_mode=InputMode.SELECTION)
    def _(event):
        line.cursor_down(count=event.arg)

    @handle(Keys.Up, in_mode=InputMode.COMPLETE)
    def _(event):
        line.complete_previous()

    @handle(Keys.Down, in_mode=InputMode.COMPLETE)
    def _(event):
        line.complete_next()

    @handle(Keys.ControlH, in_mode=InputMode.INSERT)
    @handle(Keys.Backspace, in_mode=InputMode.INSERT)
    @handle(Keys.ControlH, in_mode=InputMode.COMPLETE)
    @handle(Keys.Backspace, in_mode=InputMode.COMPLETE)
    def _(event):
        line.delete_before_cursor(count=event.arg)

        # Quit autocomplete mode.
        if event.input_processor.input_mode == InputMode.COMPLETE:
            event.input_processor.pop_input_mode()

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

        # Quit autocomplete mode.
        if event.input_processor.input_mode == InputMode.COMPLETE:
            event.input_processor.pop_input_mode()

    @handle(Keys.Escape, in_mode=InputMode.COMPLETE)
    @handle(Keys.ControlC, in_mode=InputMode.COMPLETE)
    def _(event):
        """
        Pressing escape or Ctrl-C in complete mode, goes back to default mode.
        """
        event.input_processor.pop_input_mode()
