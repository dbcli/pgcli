from __future__ import unicode_literals

from ..keys import Keys
from ..enums import InputMode
from ..line import ClipboardData

from .utils import create_handle_decorator


def basic_bindings(registry, cli_ref):
    cli = cli_ref()
    line = cli_ref().line
    renderer = cli_ref().renderer
    handle = create_handle_decorator(registry, line)

    @handle(Keys.ControlA)
    @handle(Keys.ControlB)
    @handle(Keys.ControlC)
    @handle(Keys.ControlD)
    @handle(Keys.ControlE)
    @handle(Keys.ControlF)
    @handle(Keys.ControlG)
    @handle(Keys.ControlH)
    @handle(Keys.ControlI)
    @handle(Keys.ControlJ)
    @handle(Keys.ControlK)
    @handle(Keys.ControlL)
    @handle(Keys.ControlM)
    @handle(Keys.ControlN)
    @handle(Keys.ControlO)
    @handle(Keys.ControlP)
    @handle(Keys.ControlQ)
    @handle(Keys.ControlR)
    @handle(Keys.ControlS)
    @handle(Keys.ControlT)
    @handle(Keys.ControlU)
    @handle(Keys.ControlV)
    @handle(Keys.ControlW)
    @handle(Keys.ControlX)
    @handle(Keys.ControlY)
    @handle(Keys.ControlZ)
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
    @handle(Keys.ControlUnderscore)
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

        If people want to insert these characters as a literal, they can always
        do by doing a quoted insert. (ControlQ in emacs mode, ControlV in Vi
        mode.)
        """
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
        cli.set_abort()

    @handle(Keys.ControlD)
    def _(event):
        # When there is text, act as delete, otherwise call exit.
        if line.text:
            line.delete()
        else:
            cli.set_exit()

    @handle(Keys.ControlE)
    def _(event):
        line.cursor_position += line.document.get_end_of_line_position()

    @handle(Keys.ControlI, in_mode=InputMode.INSERT)
    def _(event):
        r"""
        Ctrl-I is identical to "\t"

        Traditional tab-completion, where the first tab completes the common
        suffix and the second tab lists all the completions.
        """
        def second_tab():
            line.complete_next(start_at_first=False)

        # On the second tab-press, or when already navigating through
        # completions.
        if event.second_press or (line.complete_state and line.complete_state.complete_index is not None):
            second_tab()
        else:
            # On the first tab press, only complete the common parts of all completions.
            has_common = line.complete_common()
            if not has_common:
                second_tab()

    @handle(Keys.BackTab, in_mode=InputMode.INSERT)
    def _(event):
        """
        Shift+Tab: go to previous completion.
        """
        line.complete_previous()

    @handle(Keys.ControlJ, in_mode=InputMode.INSERT)
    @handle(Keys.ControlM, in_mode=InputMode.INSERT)
    def _(event):
        """
        Newline/Enter. (Or return input.)
        """
        if line.is_multiline:
            line.newline()
        else:
            if line.validate():
                cli_ref().line.add_to_history()
                cli_ref().set_return_value(line.document)

    @handle(Keys.ControlK, in_mode=InputMode.INSERT)
    def _(event):
        deleted = line.delete(count=line.document.get_end_of_line_position())
        line.set_clipboard(ClipboardData(deleted))

    @handle(Keys.ControlL)
    def _(event):
        renderer.clear()

    @handle(Keys.ControlT, in_mode=InputMode.INSERT)
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

    @handle(Keys.PageUp, in_mode=InputMode.INSERT)
    def _(event):
        line.history_backward()

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

    @handle(Keys.Any, in_mode=InputMode.INSERT)
    def _(event):
        """
        Insert data at cursor position.
        """
        line.insert_text(event.data * event.arg)

    @handle(Keys.CPRResponse)
    def _(event):
        """
        Handle incoming Cursor-Position-Request response.
        """
        # The incoming data looks like u'\x1b[35;1R'
        # Parse row/col information.
        row, col = map(int, event.data[2:-1].split(';'))

        # Report absolute cursor position to the renderer.
        cli_ref().renderer.report_absolute_cursor_row(row)
