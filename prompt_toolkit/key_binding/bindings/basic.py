# pylint: disable=function-redefined
from __future__ import unicode_literals

from prompt_toolkit.keys import Keys
from prompt_toolkit.filters import CLIFilter, Always, HasSelection, Condition
from prompt_toolkit.enums import DEFAULT_BUFFER

from .utils import create_handle_decorator


__all__ = (
    'load_basic_bindings',
    'load_basic_system_bindings',
)


def load_basic_bindings(registry, filter=Always()):
    assert isinstance(filter, CLIFilter)

    handle = create_handle_decorator(registry, filter)
    has_selection = HasSelection()

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
    @handle(Keys.ControlLeft)
    @handle(Keys.ControlRight)
    @handle(Keys.ControlUp)
    @handle(Keys.ControlDown)
    def _(event):
        """
        First, for any of these keys, Don't do anything by default. Also don't
        catch them in the 'Any' handler which will insert them as data.

        If people want to insert these characters as a literal, they can always
        do by doing a quoted insert. (ControlQ in emacs mode, ControlV in Vi
        mode.)
        """
        pass

    @handle(Keys.Home)
    def _(event):
        b = event.current_buffer
        b.cursor_position += b.document.get_start_of_line_position()

    @handle(Keys.End)
    def _(event):
        b = event.current_buffer
        b.cursor_position += b.document.get_end_of_line_position()

    # CTRL keys.

    @handle(Keys.ControlC)
    def _(event):
        """
        Abort when Control-C has been pressed.
        """
        event.cli.set_abort()

    @handle(Keys.ControlD, filter=Condition(lambda cli: cli.current_buffer.text))
    def _(event):
        """
        Delete text before cursor.
        """
        event.current_buffer.delete(event.arg)

    @handle(Keys.ControlD, filter=Condition(lambda cli:
        cli.current_buffer_name == DEFAULT_BUFFER and
        not cli.current_buffer.text))
    def _(event):
        """
        Exit on Control-D when the input is empty.
        """
        event.cli.set_exit()

    @handle(Keys.ControlI, filter= ~has_selection)
    def _(event):
        r"""
        Ctrl-I is identical to "\t"

        Traditional tab-completion, where the first tab completes the common
        suffix and the second tab lists all the completions.
        """
        b = event.current_buffer

        def second_tab():
            if b.complete_state:
                b.complete_next()
            else:
                event.cli.start_completion(select_first=True)

        # On the second tab-press, or when already navigating through
        # completions.
        if event.second_press or b.complete_state:
            second_tab()
        else:
            event.cli.start_completion(insert_common_part=True)

    @handle(Keys.BackTab, filter= ~has_selection)
    def _(event):
        """
        Shift+Tab: go to previous completion.
        """
        event.current_buffer.complete_previous()

    @handle(Keys.ControlJ, filter= ~has_selection)
    def _(event):
        """
        Newline/Enter. (Or return input.)
        """
        b = event.current_buffer

        if b.is_multiline():
            b.newline(copy_margin=not event.cli.in_paste_mode)
        else:
            if b.accept_action.is_returnable:
                b.accept_action.validate_and_handle(event.cli, b)

    @handle(Keys.ControlK, filter= ~has_selection)
    def _(event):
        buffer = event.current_buffer
        deleted = buffer.delete(count=buffer.document.get_end_of_line_position())
        event.cli.clipboard.set_text(deleted)

    @handle(Keys.ControlT, filter= ~has_selection)
    def _(event):
        event.current_buffer.swap_characters_before_cursor()

    @handle(Keys.ControlU, filter= ~has_selection)
    def _(event):
        """
        Clears the line before the cursor position. If you are at the end of
        the line, clears the entire line.
        """
        buffer = event.current_buffer
        deleted = buffer.delete_before_cursor(count=-buffer.document.get_start_of_line_position())
        event.cli.clipboard.set_text(deleted)

    @handle(Keys.ControlW, filter= ~has_selection)
    def _(event):
        """
        Delete the word before the cursor.
        """
        buffer = event.current_buffer
        pos = buffer.document.find_start_of_previous_word(count=event.arg)

        if pos:
            deleted = buffer.delete_before_cursor(count=-pos)
            event.cli.clipboard.set_text(deleted)

    @handle(Keys.PageUp, filter= ~has_selection)
    def _(event):
        event.current_buffer.history_backward()

    @handle(Keys.PageDown, filter= ~has_selection)
    def _(event):
        event.current_buffer.history_forward()

    @handle(Keys.Left)
    def _(event):
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.get_cursor_left_position(count=event.arg)

    @handle(Keys.Right)
    def _(event):
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.get_cursor_right_position(count=event.arg)

    @handle(Keys.Up, filter= ~has_selection)
    def _(event):
        event.current_buffer.auto_up(count=event.arg)

    @handle(Keys.Up, filter=has_selection)
    def _(event):
        event.current_buffer.cursor_up(count=event.arg)

    @handle(Keys.Down, filter= ~has_selection)
    def _(event):
        event.current_buffer.auto_down(count=event.arg)

    @handle(Keys.Down, filter=has_selection)
    def _(event):
        event.current_buffer.cursor_down(count=event.arg)

    @handle(Keys.ControlH, filter= ~has_selection)
    @handle(Keys.Backspace, filter= ~has_selection)
    def _(event):
        buffer = event.current_buffer
        buffer.delete_before_cursor(count=event.arg)

    @handle(Keys.Delete, filter= ~has_selection)
    def _(event):
        event.current_buffer.delete(count=event.arg)

    @handle(Keys.ShiftDelete, filter= ~has_selection)
    def _(event):
        event.current_buffer.delete(count=event.arg)

    @handle(Keys.Any, filter= ~has_selection)
    def _(event):
        """
        Insert data at cursor position.
        """
        event.current_buffer.insert_text(event.data * event.arg)

    # Global bindings. These are never disabled and don't include the default filter.

    @registry.add_binding(Keys.ControlL)
    def _(event):
        " Clear whole screen and redraw. "
        event.cli.renderer.clear()

    @registry.add_binding(Keys.CPRResponse)
    def _(event):
        """
        Handle incoming Cursor-Position-Request response.
        """
        # The incoming data looks like u'\x1b[35;1R'
        # Parse row/col information.
        row, col = map(int, event.data[2:-1].split(';'))

        # Report absolute cursor position to the renderer.
        event.cli.renderer.report_absolute_cursor_row(row)


def load_basic_system_bindings(registry, filter=Always()):
    """
    Basic system bindings (For both Emacs and Vi mode.)
    """
    assert isinstance(filter, CLIFilter)
    handle = create_handle_decorator(registry, filter)

    @handle(Keys.ControlZ)
    def _(event):
        """
        Suspend process to background.
        """
        event.cli.suspend_to_background()
