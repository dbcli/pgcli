# pylint: disable=function-redefined
from __future__ import unicode_literals
from prompt_toolkit.buffer import SelectionType, indent, unindent
from prompt_toolkit.keys import Keys
from prompt_toolkit.enums import IncrementalSearchDirection, SEARCH_BUFFER, SYSTEM_BUFFER
from prompt_toolkit.filters import Always, Condition, EmacsMode, to_cli_filter, HasSelection, EmacsInsertMode, HasFocus
from prompt_toolkit.completion import CompleteEvent

from .utils import create_handle_decorator
from .scroll import scroll_page_up, scroll_page_down

from six.moves import range

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
    filter = to_cli_filter(filter)

    handle = create_handle_decorator(registry, filter & EmacsMode())
    insert_mode = EmacsInsertMode()
    has_selection = HasSelection()

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

    @handle(Keys.ControlO, filter=insert_mode)
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

    @handle(Keys.ControlY, filter=insert_mode)
    @handle(Keys.ControlX, 'r', 'y', filter=insert_mode)
    def _(event):
        """
        Paste before cursor.
        """
        event.current_buffer.paste_clipboard_data(
            event.cli.clipboard.get_data(), count=event.arg, before=True)

    @handle(Keys.ControlUnderscore, save_before=(lambda e: False), filter=insert_mode)
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

    is_returnable = Condition(
        lambda cli: cli.current_buffer.accept_action.is_returnable)

    @handle(Keys.Escape, Keys.ControlJ, filter=insert_mode & is_returnable)
    def _(event):
        """
        Meta + Newline: always accept input.
        """
        b = event.current_buffer
        b.accept_action.validate_and_handle(event.cli, b)

    @handle(Keys.ControlSquareClose, Keys.Any)
    def _(event):
        """
        When Ctl-] + a character is pressed. go to that character.
        """
        match = event.current_buffer.document.find(event.data, in_current_line=True, count=(event.arg))
        if match is not None:
            event.current_buffer.cursor_position += match

    @handle(Keys.Escape, Keys.Backspace, filter=insert_mode)
    def _(event):
        """
        Delete word backwards.
        """
        buffer = event.current_buffer
        pos = buffer.document.find_start_of_previous_word(count=event.arg)

        if pos is None:
            # Nothing found. Only whitespace before the cursor?
            pos = - buffer.cursor_position

        if pos:
            deleted = buffer.delete_before_cursor(count=-pos)
            event.cli.clipboard.set_text(deleted)

    @handle(Keys.ControlDelete, filter=insert_mode)
    def _(event):
        """
        Delete word after cursor.
        """
        buff = event.current_buffer
        pos = buff.document.find_next_word_ending(count=event.arg)

        if pos:
            deleted = buff.delete(count=pos)
            event.cli.clipboard.set_text(deleted)

    @handle(Keys.Escape, 'a')
    def _(event):
        """
        Previous sentence.
        """
        # TODO:
        pass

    @handle(Keys.Escape, 'c', filter=insert_mode)
    def _(event):
        """
        Capitalize the current (or following) word.
        """
        buffer = event.current_buffer

        for i in range(event.arg):
            pos = buffer.document.find_next_word_ending()
            words = buffer.document.text_after_cursor[:pos]
            buffer.insert_text(words.title(), overwrite=True)

    @handle(Keys.Escape, 'd', filter=insert_mode)
    def _(event):
        """
        Delete word forwards.
        """
        buffer = event.current_buffer
        pos = buffer.document.find_next_word_ending(count=event.arg)

        if pos:
            deleted = buffer.delete(count=pos)
            event.cli.clipboard.set_text(deleted)

    @handle(Keys.Escape, 'e')
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

    @handle(Keys.Escape, 'l', filter=insert_mode)
    def _(event):
        """
        Lowercase the current (or following) word.
        """
        buffer = event.current_buffer

        for i in range(event.arg):  # XXX: not DRY: see meta_c and meta_u!!
            pos = buffer.document.find_next_word_ending()
            words = buffer.document.text_after_cursor[:pos]
            buffer.insert_text(words.lower(), overwrite=True)

    @handle(Keys.Escape, 't', filter=insert_mode)
    def _(event):
        """
        Swap the last two words before the cursor.
        """
        # TODO

    @handle(Keys.Escape, 'u', filter=insert_mode)
    def _(event):
        """
        Uppercase the current (or following) word.
        """
        buffer = event.current_buffer

        for i in range(event.arg):
            pos = buffer.document.find_next_word_ending()
            words = buffer.document.text_after_cursor[:pos]
            buffer.insert_text(words.upper(), overwrite=True)

    @handle(Keys.Escape, '.', filter=insert_mode)
    def _(event):
        """
        Rotate through the last word (white-space delimited) of the previous lines in history.
        """
        # TODO

    @handle(Keys.Escape, '\\', filter=insert_mode)
    def _(event):
        """
        Delete all spaces and tabs around point.
        (delete-horizontal-space)
        """
        buff = event.current_buffer
        text_before_cursor = buff.document.text_before_cursor
        text_after_cursor = buff.document.text_after_cursor

        delete_before = len(text_before_cursor) - len(text_before_cursor.rstrip('\t '))
        delete_after = len(text_after_cursor) - len(text_after_cursor.lstrip('\t '))

        buff.delete_before_cursor(count=delete_before)
        buff.delete(count=delete_after)

    @handle(Keys.Escape, '*', filter=insert_mode)
    def _(event):
        """
        `meta-*`: Insert all possible completions of the preceding text.
        """
        buff = event.current_buffer

        # List all completions.
        complete_event = CompleteEvent(text_inserted=False, completion_requested=True)
        completions = list(buff.completer.get_completions(buff.document, complete_event))

        # Insert them.
        text_to_insert = ' '.join(c.text for c in completions)
        buff.insert_text(text_to_insert)

    @handle(Keys.ControlX, Keys.ControlU, save_before=(lambda e: False), filter=insert_mode)
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
        Start of the selection (if the current buffer is not empty).
        """
        # Take the current cursor position as the start of this selection.
        buff = event.current_buffer
        if buff.text:
            buff.start_selection(selection_type=SelectionType.CHARACTERS)

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

    @handle(Keys.Escape, '/', filter=insert_mode)
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

        indent(buffer, from_, to + 1, count=event.arg)

    @handle(Keys.ControlC, '<', filter=has_selection)
    def _(event):
        """
        Unindent selected text.
        """
        buffer = event.current_buffer

        from_, to = buffer.document.selection_range()
        from_, _ = buffer.document.translate_index_to_position(from_)
        to, _ = buffer.document.translate_index_to_position(to)

        unindent(buffer, from_, to + 1, count=event.arg)


def load_emacs_open_in_editor_bindings(registry, filter=None):
    """
    Pressing C-X C-E will open the buffer in an external editor.
    """
    handle = create_handle_decorator(registry, filter & EmacsMode())
    has_selection = HasSelection()

    @handle(Keys.ControlX, Keys.ControlE, filter= ~has_selection)
    def _(event):
        """
        Open editor.
        """
        event.current_buffer.open_in_editor(event.cli)


def load_emacs_system_bindings(registry, filter=None):
    handle = create_handle_decorator(registry, filter & EmacsMode())
    has_focus = HasFocus(SYSTEM_BUFFER)

    @handle(Keys.Escape, '!', filter= ~has_focus)
    def _(event):
        """
        M-'!' opens the system prompt.
        """
        event.cli.push_focus(SYSTEM_BUFFER)

    @handle(Keys.Escape, filter=has_focus)
    @handle(Keys.ControlG, filter=has_focus)
    @handle(Keys.ControlC, filter=has_focus)
    def _(event):
        """
        Cancel system prompt.
        """
        event.cli.buffers[SYSTEM_BUFFER].reset()
        event.cli.pop_focus()

    @handle(Keys.ControlJ, filter=has_focus)
    def _(event):
        """
        Run system command.
        """
        system_line = event.cli.buffers[SYSTEM_BUFFER]
        event.cli.run_system_command(system_line.text)
        system_line.reset(append_to_history=True)

        # Focus previous buffer again.
        event.cli.pop_focus()


def load_emacs_search_bindings(registry, get_search_state=None, filter=None):
    filter = to_cli_filter(filter)

    handle = create_handle_decorator(registry, filter & EmacsMode())
    has_focus = HasFocus(SEARCH_BUFFER)

    assert get_search_state is None or callable(get_search_state)

    if not get_search_state:
        def get_search_state(cli): return cli.search_state

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
        event.cli.pop_focus()

    @handle(Keys.ControlJ, filter=has_focus)
    def _(event):
        """
        When enter pressed in isearch, quit isearch mode. (Multiline
        isearch would be too complicated.)
        """
        input_buffer = event.cli.buffers.previous(event.cli)
        search_buffer = event.cli.buffers[SEARCH_BUFFER]

        # Update search state.
        if search_buffer.text:
            get_search_state(event.cli).text = search_buffer.text

        # Apply search.
        input_buffer.apply_search(get_search_state(event.cli), include_current_position=True)

        # Add query to history of search line.
        search_buffer.append_to_history()
        search_buffer.reset()

        # Focus previous document again.
        event.cli.pop_focus()

    @handle(Keys.ControlR, filter= ~has_focus)
    def _(event):
        get_search_state(event.cli).direction = IncrementalSearchDirection.BACKWARD
        event.cli.push_focus(SEARCH_BUFFER)

    @handle(Keys.ControlS, filter= ~has_focus)
    def _(event):
        get_search_state(event.cli).direction = IncrementalSearchDirection.FORWARD
        event.cli.push_focus(SEARCH_BUFFER)

    def incremental_search(cli, direction, count=1):
        " Apply search, but keep search buffer focussed. "
        # Update search_state.
        search_state = get_search_state(cli)
        direction_changed = search_state.direction != direction

        search_state.text = cli.buffers[SEARCH_BUFFER].text
        search_state.direction = direction

        # Apply search to current buffer.
        if not direction_changed:
            input_buffer = cli.buffers.previous(cli)
            input_buffer.apply_search(search_state,
                                      include_current_position=False, count=count)

    @handle(Keys.ControlR, filter=has_focus)
    @handle(Keys.Up, filter=has_focus)
    def _(event):
        incremental_search(event.cli, IncrementalSearchDirection.BACKWARD, count=event.arg)

    @handle(Keys.ControlS, filter=has_focus)
    @handle(Keys.Down, filter=has_focus)
    def _(event):
        incremental_search(event.cli, IncrementalSearchDirection.FORWARD, count=event.arg)


def load_extra_emacs_page_navigation_bindings(registry, filter=None):
    """
    Key bindings, for scrolling up and down through pages.
    This are separate bindings, because GNU readline doesn't have them.
    """
    filter = to_cli_filter(filter)
    handle = create_handle_decorator(registry, filter & EmacsMode())

    handle(Keys.ControlV)(scroll_page_down)
    handle(Keys.PageDown)(scroll_page_down)
    handle(Keys.Escape, 'v')(scroll_page_up)
    handle(Keys.PageUp)(scroll_page_up)
