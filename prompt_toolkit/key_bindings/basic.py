from __future__ import unicode_literals

from ..keys import Key
from ..enums import InputMode, IncrementalSearchDirection
from ..line import ClipboardData

from .utils import create_handle_decorator


def basic_bindings(registry, cli_ref):
    line = cli_ref().line
    handle = create_handle_decorator(registry, line)

    @handle(Key.Home)
    def _(event):
        line.cursor_position += line.document.home_position

    @handle(Key.End)
    def _(event):
        line.cursor_position += line.document.end_position

    # CTRL keys.

    @handle(Key.ControlA)
    def _(event):
        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=False)

    @handle(Key.ControlB)
    def _(event):
        line.cursor_position += line.document.get_cursor_left_position(count=event.arg)

    @handle(Key.ControlC)
    def _(event):
        line.abort()

    @handle(Key.ControlD)
    def _(event):
        # When there is text, act as delete, otherwise call exit.
        if line.text:
            line.delete()
        else:
            line.exit()

    @handle(Key.ControlE)
    def _(event):
        line.cursor_position += line.document.get_end_of_line_position()

    @handle(Key.ControlF)
    def _(event):
        line.cursor_position += line.document.get_cursor_right_position(count=event.arg)

    @handle(Key.ControlG)
    def _(event):
        pass

    @handle(Key.ControlG, in_mode=InputMode.INCREMENTAL_SEARCH)
    # NOTE: the reason for not binding Escape to this one, is that we want
    #       Alt+Enter to accept input directly in incremental search mode.
    def _(event):
        """
        Abort an incremental search and restore the original line.
        """
        line.exit_isearch(restore_original_line=True)
        event.input_processor.pop_input_mode()

    @handle(Key.ControlI)
    @handle(Key.Tab)
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


    @handle(Key.ControlJ, in_mode=InputMode.INCREMENTAL_SEARCH)
    @handle(Key.ControlM, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        """
        When enter pressed in isearch, quit isearch mode. (Multiline
        isearch would be too complicated.)
        """
        line.exit_isearch()
        event.input_processor.pop_input_mode()

    @handle(Key.ControlJ)
    @handle(Key.ControlM)
    def _(event):
        """
        Newline/Enter.
        """
        if line.is_multiline:
            line.newline()
        else:
            line.return_input()

    @handle(Key.ControlK)
    def _(event):
        deleted = line.delete(count=line.document.get_end_of_line_position())
        line.set_clipboard(ClipboardData(deleted))

    @handle(Key.ControlL)
    def _(event):
        line.clear()

    @handle(Key.ControlN)
    def _(event):
        line.history_forward()

    @handle(Key.ControlO)
    def _(event):
        pass

    @handle(Key.ControlP)
    def _(event):
        line.history_backward()

    @handle(Key.ControlQ)
    def _(event):
        pass

    @handle(Key.ControlR)
    @handle(Key.Up, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        line.incremental_search(IncrementalSearchDirection.BACKWARD)

        if event.input_processor.input_mode != InputMode.INCREMENTAL_SEARCH:
            event.input_processor.push_input_mode(InputMode.INCREMENTAL_SEARCH)

    @handle(Key.ControlS)
    @handle(Key.Down, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        line.incremental_search(IncrementalSearchDirection.FORWARD)

        if event.input_processor.input_mode != InputMode.INCREMENTAL_SEARCH:
            event.input_processor.push_input_mode(InputMode.INCREMENTAL_SEARCH)

    @handle(Key.ControlT)
    def _(event):
        line.swap_characters_before_cursor()

    @handle(Key.ControlU)
    def _(event):
        """
        Clears the line before the cursor position. If you are at the end of
        the line, clears the entire line.
        """
        deleted = line.delete_before_cursor(count=-line.document.get_start_of_line_position())
        line.set_clipboard(ClipboardData(deleted))

    @handle(Key.ControlV)
    def _(event):
        pass

    @handle(Key.ControlW)
    def _(event):
        """
        Delete the word before the cursor.
        """
        pos = line.document.find_start_of_previous_word(count=event.arg)
        if pos:
            deleted = line.delete_before_cursor(count=-pos)
            line.set_clipboard(ClipboardData(deleted))

    @handle(Key.ControlX)
    def _(event):
        pass

    @handle(Key.ControlY)
    def _(event):
        # Pastes the clipboard content.
        line.paste_from_clipboard()

    @handle(Key.ControlZ)
    def _(event):
        pass

    @handle(Key.PageUp, in_mode=InputMode.COMPLETE)
    def _(event):
        line.complete_previous(5)

    @handle(Key.PageUp)
    def _(event):
        line.history_backward()

    @handle(Key.PageDown, in_mode=InputMode.COMPLETE)
    def _(event):
        line.complete_next(5)

    @handle(Key.PageDown)
    def _(event):
        line.history_forward()

    @handle(Key.Left)
    def _(event):
        if not event.input_processor.input_mode == InputMode.INCREMENTAL_SEARCH:
            line.cursor_position += line.document.get_cursor_left_position(count=event.arg)

    @handle(Key.Right)
    def _(event):
        if not event.input_processor.input_mode == InputMode.INCREMENTAL_SEARCH:
            line.cursor_position += line.document.get_cursor_right_position(count=event.arg)

    @handle(Key.Up)
    def _(event):
        line.auto_up(count=event.arg)

    @handle(Key.Down)
    def _(event):
        line.auto_down(count=event.arg)

    @handle(Key.ControlH)
    @handle(Key.Backspace)
    def _(event):
        line.delete_before_cursor(count=event.arg)

    @handle(Key.ControlH, in_mode=InputMode.INCREMENTAL_SEARCH)
    @handle(Key.Backspace, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        line.isearch_delete_before_cursor(count=event.arg)

    @handle(Key.Delete)
    def _(event):
        line.delete(count=event.arg)

    @handle(Key.ShiftDelete)
    def _(event):
        line.delete(count=event.arg)

    @handle(Key.Any, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        """
        Insert isearch string.
        """
        line.insert_isearch_text(event.data)

    @handle(Key.Any, in_mode=InputMode.COMPLETE)
    @handle(Key.Any)
    def _(event):
        """
        Insert data at cursor position.
        """
        line.insert_text(event.data * event.arg)

        # Always quit autocomplete mode when the text changes.
        if event.input_processor.input_mode == InputMode.COMPLETE:
            event.input_processor.pop_input_mode()

    @handle(Key.Escape, Key.Left)
    def _(event):
        """
        Cursor to start of previous word.
        """
        line.cursor_position += line.document.find_previous_word_beginning(count=event.arg) or 0

    @handle(Key.Escape, Key.Right)
    def _(event):
        """
        Cursor to start of next word.
        """
        line.cursor_position += line.document.find_next_word_beginning(count=event.arg) or 0

    @handle(Key.Escape, in_mode=InputMode.COMPLETE)
    @handle(Key.ControlC, in_mode=InputMode.COMPLETE)
    def _(event):
        """
        Pressing escape or Ctrl-C in complete mode, goes back to default mode.
        """
        event.input_processor.pop_input_mode()
