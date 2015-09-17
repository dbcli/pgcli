# pylint: disable=function-redefined
from __future__ import unicode_literals
from prompt_toolkit.buffer import SelectionType, indent, unindent
from prompt_toolkit.keys import Keys
from prompt_toolkit.enums import IncrementalSearchDirection, SEARCH_BUFFER, SYSTEM_BUFFER
from prompt_toolkit.filters import CLIFilter, Always

from .utils import create_handle_decorator
from .scroll import scroll_page_up, scroll_page_down

import prompt_toolkit.filters as filters

__all__ = (
    'load_emacs_bindings',
    'load_emacs_search_bindings',
    'load_emacs_system_bindings',
    'load_extra_emacs_page_navigation_bindings',
)


def load_emacs_bindings(registry, filter=Always()):
    """
    Some e-macs extensions.
    """
    # Overview of Readline emacs commands:
    # http://www.catonmat.net/download/readline-emacs-editing-mode-cheat-sheet.pdf

    assert isinstance(filter, CLIFilter)

    handle = create_handle_decorator(registry, filter)
    has_selection = filters.HasSelection()

    @handle(Keys.Escape)
    def _(event):
        """
        By default, ignore escape key.

        (If we don't put this here, and Esc is followed by a key which sequence
        is not handled, we'll insert an Escape character in the input stream.
        Something we don't want and happens to easily in emacs mode.
        Further, people can always use ControlQ to do a quoted insert.)
        """
        pass

    @handle(Keys.ControlA)
    def _(event):
        """
        Start of line.
        """
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.get_start_of_line_position(after_whitespace=False)

    @handle(Keys.ControlB)
    def _(event):
        """
        Character back.
        """
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.get_cursor_left_position(count=event.arg)

    @handle(Keys.ControlE)
    def _(event):
        """
        End of line.
        """
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.get_end_of_line_position()

    @handle(Keys.ControlF)
    def _(event):
        """
        Character forward.
        """
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.get_cursor_right_position(count=event.arg)

    @handle(Keys.ControlN, filter= ~has_selection)
    def _(event):
        """
        Next line.
        """
        event.current_buffer.auto_down()

    @handle(Keys.ControlN, filter=has_selection)
    def _(event):
        """
        Next line.
        """
        event.current_buffer.cursor_down()

    @handle(Keys.ControlO, filter= ~has_selection)
    def _(event):
        """
        Insert newline, but don't move the cursor.
        """
        event.current_buffer.insert_text('\n', move_cursor=False)

    @handle(Keys.ControlP, filter= ~has_selection)
    def _(event):
        """
        Previous line.
        """
        event.current_buffer.auto_up(count=event.arg)

    @handle(Keys.ControlP, filter=has_selection)
    def _(event):
        """
        Previous line.
        """
        event.current_buffer.cursor_up(count=event.arg)

    @handle(Keys.ControlQ, Keys.Any, filter= ~has_selection)
    def _(event):
        """
        Quoted insert.

        For vt100 terminals, you have to disable flow control by running
        ``stty -ixon``, otherwise Ctrl-Q and Ctrl-S are captured by the
        terminal.
        """
        event.current_buffer.insert_text(event.data, overwrite=False)

    @handle(Keys.ControlY, filter= ~has_selection)
    @handle(Keys.ControlX, 'r', 'y', filter= ~has_selection)
    def _(event):
        """
        Paste before cursor.
        """
        event.current_buffer.paste_clipboard_data(
            event.cli.clipboard.get_data(), count=event.arg, before=True)

    @handle(Keys.ControlUnderscore, save_before=(lambda e: False), filter= ~has_selection)
    def _(event):
        """
        Undo.
        """
        event.current_buffer.undo()

    def handle_digit(c):
        """
        Handle Alt + digit in the `meta_digit` method.
        """
        @handle(Keys.Escape, c)
        def _(event):
            event.append_to_arg_count(c)

    for c in '0123456789':
        handle_digit(c)

    @handle(Keys.Escape, '-')
    def _(event):
        """
        """
        if event._arg is None:
            event.append_to_arg_count('-')

    @handle(Keys.Escape, Keys.ControlJ, filter= ~has_selection)
    def _(event):
        """
        Meta + Newline: always accept input.
        """
        b = event.current_buffer

        if b.accept_action.is_returnable:
            b.accept_action.validate_and_handle(event.cli, b)

    @handle(Keys.ControlSquareClose, Keys.Any)
    def _(event):
        """
        When Ctl-] + a character is pressed. go to that character.
        """
        match = event.current_buffer.document.find(event.data, in_current_line=True, count=(event.arg))
        if match is not None:
            event.current_buffer.cursor_position += match

    @handle(Keys.Escape, Keys.Backspace, filter= ~has_selection)
    def _(event):
        """
        Delete word backwards.
        """
        buffer = event.current_buffer
        pos = buffer.document.find_start_of_previous_word(count=event.arg)

        if pos:
            deleted = buffer.delete_before_cursor(count=-pos)
            event.cli.clipboard.set_text(deleted)

    @handle(Keys.Escape, 'a', filter= ~has_selection)
    def _(event):
        """
        Previous sentence.
        """
        # TODO:
        pass

    @handle(Keys.Escape, 'c', filter= ~has_selection)
    def _(event):
        """
        Capitalize the current (or following) word.
        """
        buffer = event.current_buffer

        for i in range(event.arg):
            pos = buffer.document.find_next_word_ending()
            words = buffer.document.text_after_cursor[:pos]
            buffer.insert_text(words.title(), overwrite=True)

    @handle(Keys.Escape, 'd', filter= ~has_selection)
    def _(event):
        """
        Delete word forwards.
        """
        buffer = event.current_buffer
        pos = buffer.document.find_next_word_ending(count=event.arg)

        if pos:
            deleted = buffer.delete(count=pos)
            event.cli.clipboard.set_text(deleted)

    @handle(Keys.Escape, 'e', filter= ~has_selection)
    def _(event):
        """ Move to end of sentence. """
        # TODO:
        pass

    @handle(Keys.Escape, 'f')
    @handle(Keys.ControlRight)
    def _(event):
        """
        Cursor to end of next word.
        """
        buffer= event.current_buffer
        pos = buffer.document.find_next_word_ending(count=event.arg)

        if pos:
            buffer.cursor_position += pos

    @handle(Keys.Escape, 'b')
    @handle(Keys.ControlLeft)
    def _(event):
        """
        Cursor to start of previous word.
        """
        buffer = event.current_buffer
        pos = buffer.document.find_previous_word_beginning(count=event.arg)
        if pos:
            buffer.cursor_position += pos

    @handle(Keys.Escape, 'l', filter= ~has_selection)
    def _(event):
        """
        Lowercase the current (or following) word.
        """
        buffer = event.current_buffer

        for i in range(event.arg):  # XXX: not DRY: see meta_c and meta_u!!
            pos = buffer.document.find_next_word_ending()
            words = buffer.document.text_after_cursor[:pos]
            buffer.insert_text(words.lower(), overwrite=True)

    @handle(Keys.Escape, 't', filter= ~has_selection)
    def _(event):
        """
        Swap the last two words before the cursor.
        """
        # TODO

    @handle(Keys.Escape, 'u', filter= ~has_selection)
    def _(event):
        """
        Uppercase the current (or following) word.
        """
        buffer = event.current_buffer

        for i in range(event.arg):
            pos = buffer.document.find_next_word_ending()
            words = buffer.document.text_after_cursor[:pos]
            buffer.insert_text(words.upper(), overwrite=True)

    @handle(Keys.Escape, '.', filter= ~has_selection)
    def _(event):
        """
        Rotate through the last word (white-space delimited) of the previous lines in history.
        """
        # TODO

    @handle(Keys.Escape, '\\', filter= ~has_selection)
    def _(event):
        """
        Delete all spaces and tabs around point.
        (delete-horizontal-space)
        """

    @handle(Keys.Escape, '*', filter= ~has_selection)
    def _(event):
        """
        `meta-*`: Insert all possible completions of the preceding text.
        """

    @handle(Keys.ControlX, Keys.ControlU, save_before=(lambda e: False), filter= ~has_selection)
    def _(event):
        event.current_buffer.undo()

    @handle(Keys.ControlX, Keys.ControlX)
    def _(event):
        """
        Move cursor back and forth between the start and end of the current
        line.
        """
        buffer = event.current_buffer

        if buffer.document.current_char == '\n':
            buffer.cursor_position += buffer.document.get_start_of_line_position(after_whitespace=False)
        else:
            buffer.cursor_position += buffer.document.get_end_of_line_position()

    @handle(Keys.ControlSpace)
    def _(event):
        """
        Start of the selection.
        """
        # Take the current cursor position as the start of this selection.
        event.current_buffer.start_selection(selection_type=SelectionType.CHARACTERS)

    @handle(Keys.ControlG, filter= ~has_selection)
    def _(event):
        """
        Control + G: Cancel completion menu and validation state.
        """
        event.current_buffer.complete_state = None
        event.current_buffer.validation_error = None

    @handle(Keys.ControlG, filter=has_selection)
    def _(event):
        """
        Cancel selection.
        """
        event.current_buffer.exit_selection()

    @handle(Keys.ControlW, filter=has_selection)
    @handle(Keys.ControlX, 'r', 'k', filter=has_selection)
    def _(event):
        """
        Cut selected text.
        """
        data = event.current_buffer.cut_selection()
        event.cli.clipboard.set_data(data)

    @handle(Keys.Escape, 'w', filter=has_selection)
    def _(event):
        """
        Copy selected text.
        """
        data = event.current_buffer.copy_selection()
        event.cli.clipboard.set_data(data)

    @handle(Keys.Escape, '<', filter= ~has_selection)
    def _(event):
        """
        Move to the first line in the history.
        """
        event.current_buffer.go_to_history(0)

    @handle(Keys.Escape, '>', filter= ~has_selection)
    def _(event):
        """
        Move to the end of the input history.
        This is the line we are editing.
        """
        buffer = event.current_buffer
        buffer.go_to_history(len(buffer._working_lines) - 1)

    @handle(Keys.Escape, Keys.Left)
    def _(event):
        """
        Cursor to start of previous word.
        """
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.find_previous_word_beginning(count=event.arg) or 0

    @handle(Keys.Escape, Keys.Right)
    def _(event):
        """
        Cursor to start of next word.
        """
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.find_next_word_beginning(count=event.arg) or \
            buffer.document.get_end_of_document_position()

    @handle(Keys.Escape, '/', filter= ~has_selection)
    def _(event):
        """
        M-/: Complete.
        """
        b = event.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            event.cli.start_completion(select_first=True)

    @handle(Keys.ControlC, '>', filter=has_selection)
    def _(event):
        """
        Indent selected text.
        """
        buffer = event.current_buffer

        buffer.cursor_position += buffer.document.get_start_of_line_position(after_whitespace=True)

        from_, to = buffer.document.selection_range()
        from_, _ = buffer.document.translate_index_to_position(from_)
        to, _ = buffer.document.translate_index_to_position(to)

        indent(buffer, from_ - 1, to, count=event.arg)  # XXX: why does translate_index_to_position return 1-based indexing???

    @handle(Keys.ControlC, '<', filter=has_selection)
    def _(event):
        """
        Unindent selected text.
        """
        buffer = event.current_buffer

        from_, to = buffer.document.selection_range()
        from_, _ = buffer.document.translate_index_to_position(from_)
        to, _ = buffer.document.translate_index_to_position(to)

        unindent(buffer, from_ - 1, to, count=event.arg)


def load_emacs_open_in_editor_bindings(registry, filter=None):
    """
    Pressing C-X C-E will open the buffer in an external editor.
    """
    handle = create_handle_decorator(registry, filter)
    has_selection = filters.HasSelection()

    @handle(Keys.ControlX, Keys.ControlE, filter= ~has_selection)
    def _(event):
        """
        Open editor.
        """
        event.current_buffer.open_in_editor(event.cli)


def load_emacs_system_bindings(registry, filter=None):
    handle = create_handle_decorator(registry, filter)
    has_focus = filters.HasFocus(SYSTEM_BUFFER)

    @handle(Keys.Escape, '!', filter= ~has_focus)
    def _(event):
        """
        M-'!' opens the system prompt.
        """
        event.cli.focus_stack.push(SYSTEM_BUFFER)

    @handle(Keys.Escape, filter=has_focus)
    @handle(Keys.ControlG, filter=has_focus)
    @handle(Keys.ControlC, filter=has_focus)
    def _(event):
        """
        Cancel system prompt.
        """
        event.cli.buffers[SYSTEM_BUFFER].reset()
        event.cli.focus_stack.pop()

    @handle(Keys.ControlJ, filter=has_focus)
    def _(event):
        """
        Run system command.
        """
        system_line = event.cli.buffers[SYSTEM_BUFFER]
        event.cli.run_system_command(system_line.text)
        system_line.reset(append_to_history=True)

        # Focus previous buffer again.
        event.cli.focus_stack.pop()


def load_emacs_search_bindings(registry, filter=None):
    handle = create_handle_decorator(registry, filter)
    has_focus = filters.HasFocus(SEARCH_BUFFER)

    @handle(Keys.ControlG, filter=has_focus)
    @handle(Keys.ControlC, filter=has_focus)
    # NOTE: the reason for not also binding Escape to this one, is that we want
    #       Alt+Enter to accept input directly in incremental search mode.
    def _(event):
        """
        Abort an incremental search and restore the original line.
        """
        search_buffer = event.cli.buffers[SEARCH_BUFFER]

        search_buffer.reset()
        event.cli.focus_stack.pop()

    @handle(Keys.ControlJ, filter=has_focus)
    def _(event):
        """
        When enter pressed in isearch, quit isearch mode. (Multiline
        isearch would be too complicated.)
        """
        input_buffer = event.cli.buffers[event.cli.focus_stack.previous]
        search_buffer = event.cli.buffers[SEARCH_BUFFER]

        # Update search state.
        if search_buffer.text:
            event.cli.search_state.text = search_buffer.text

        # Apply search.
        input_buffer.apply_search(event.cli.search_state, include_current_position=True)

        # Add query to history of search line.
        search_buffer.append_to_history()
        search_buffer.reset()

        # Focus previous document again.
        event.cli.focus_stack.pop()

    @handle(Keys.ControlR, filter= ~has_focus)
    def _(event):
        event.cli.search_state.direction = IncrementalSearchDirection.BACKWARD
        event.cli.focus_stack.push(SEARCH_BUFFER)

    @handle(Keys.ControlS, filter= ~has_focus)
    def _(event):
        event.cli.search_state.direction = IncrementalSearchDirection.FORWARD
        event.cli.focus_stack.push(SEARCH_BUFFER)

    @handle(Keys.ControlR, filter=has_focus)
    @handle(Keys.Up, filter=has_focus)
    def _(event):
        # Update search_state.
        search_state = event.cli.search_state
        direction_changed = search_state.direction != IncrementalSearchDirection.BACKWARD

        search_state.text = event.cli.buffers[SEARCH_BUFFER].text
        search_state.direction = IncrementalSearchDirection.BACKWARD

        # Apply search to current buffer.
        if not direction_changed:
            input_buffer = event.cli.buffers[event.cli.focus_stack.previous]
            input_buffer.apply_search(event.cli.search_state,
                                      include_current_position=False, count=event.arg)

    @handle(Keys.ControlS, filter=has_focus)
    @handle(Keys.Down, filter=has_focus)
    def _(event):
        # Update search_state.
        search_state = event.cli.search_state
        direction_changed = search_state.direction != IncrementalSearchDirection.FORWARD

        search_state.text = event.cli.buffers[SEARCH_BUFFER].text
        search_state.direction = IncrementalSearchDirection.FORWARD

        # Apply search to current buffer.
        if not direction_changed:
            input_buffer = event.cli.buffers[event.cli.focus_stack.previous]
            input_buffer.apply_search(event.cli.search_state,
                                      include_current_position=False, count=event.arg)


def load_extra_emacs_page_navigation_bindings(registry, filter=None):
    """
    Key bindings, for scrolling up and down through pages.
    This are separate bindings, because GNU readline doesn't have them.
    """
    handle = create_handle_decorator(registry, filter)

    handle(Keys.ControlV)(scroll_page_down)
    handle(Keys.PageDown)(scroll_page_down)
    handle(Keys.Escape, 'v')(scroll_page_up)
    handle(Keys.PageUp)(scroll_page_up)
