# pylint: disable=function-redefined
from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import SelectionType, indent, unindent
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.filters import Condition, emacs_mode, has_selection, emacs_insert_mode, has_arg, is_multiline, is_read_only, vi_search_direction_reversed
from prompt_toolkit.keys import Keys

from .named_commands import get_by_name
from ..key_bindings import KeyBindings, ConditionalKeyBindings

__all__ = [
    'load_emacs_bindings',
    'load_emacs_search_bindings',
]


def load_emacs_bindings():
    """
    Some e-macs extensions.
    """
    # Overview of Readline emacs commands:
    # http://www.catonmat.net/download/readline-emacs-editing-mode-cheat-sheet.pdf
    key_bindings = KeyBindings()
    handle = key_bindings.add

    insert_mode = emacs_insert_mode

    @handle('escape')
    def _(event):
        """
        By default, ignore escape key.

        (If we don't put this here, and Esc is followed by a key which sequence
        is not handled, we'll insert an Escape character in the input stream.
        Something we don't want and happens to easily in emacs mode.
        Further, people can always use ControlQ to do a quoted insert.)
        """
        pass

    handle('c-a')(get_by_name('beginning-of-line'))
    handle('c-b')(get_by_name('backward-char'))
    handle('c-delete', filter=insert_mode)(get_by_name('kill-word'))
    handle('c-e')(get_by_name('end-of-line'))
    handle('c-f')(get_by_name('forward-char'))
    handle('c-left')(get_by_name('backward-word'))
    handle('c-right')(get_by_name('forward-word'))
    handle('c-x', 'r', 'y', filter=insert_mode)(get_by_name('yank'))
    handle('c-y', filter=insert_mode)(get_by_name('yank'))
    handle('escape', 'b')(get_by_name('backward-word'))
    handle('escape', 'c', filter=insert_mode)(get_by_name('capitalize-word'))
    handle('escape', 'd', filter=insert_mode)(get_by_name('kill-word'))
    handle('escape', 'f')(get_by_name('forward-word'))
    handle('escape', 'l', filter=insert_mode)(get_by_name('downcase-word'))
    handle('escape', 'u', filter=insert_mode)(get_by_name('uppercase-word'))
    handle('escape', 'y', filter=insert_mode)(get_by_name('yank-pop'))
    handle('escape', 'backspace', filter=insert_mode)(get_by_name('backward-kill-word'))
    handle('escape', '\\', filter=insert_mode)(get_by_name('delete-horizontal-space'))

    handle('c-_', save_before=(lambda e: False), filter=insert_mode)(
        get_by_name('undo'))

    handle('c-x', 'c-u', save_before=(lambda e: False), filter=insert_mode)(
        get_by_name('undo'))

    handle('escape', '<', filter= ~has_selection)(get_by_name('beginning-of-history'))
    handle('escape', '>', filter= ~has_selection)(get_by_name('end-of-history'))

    handle('escape', '.', filter=insert_mode)(get_by_name('yank-last-arg'))
    handle('escape', '_', filter=insert_mode)(get_by_name('yank-last-arg'))
    handle('escape', 'c-y', filter=insert_mode)(get_by_name('yank-nth-arg'))
    handle('escape', '#', filter=insert_mode)(get_by_name('insert-comment'))
    handle('c-o')(get_by_name('operate-and-get-next'))

    # ControlQ does a quoted insert. Not that for vt100 terminals, you have to
    # disable flow control by running ``stty -ixon``, otherwise Ctrl-Q and
    # Ctrl-S are captured by the terminal.
    handle('c-q', filter= ~has_selection)(get_by_name('quoted-insert'))

    handle('c-x', '(')(get_by_name('start-kbd-macro'))
    handle('c-x', ')')(get_by_name('end-kbd-macro'))
    handle('c-x', 'e')(get_by_name('call-last-kbd-macro'))

    @handle('c-n')
    def _(event):
        " Next line. "
        event.current_buffer.auto_down()

    @handle('c-p')
    def _(event):
        " Previous line. "
        event.current_buffer.auto_up(count=event.arg)

    def handle_digit(c):
        """
        Handle input of arguments.
        The first number needs to be preceded by escape.
        """
        @handle(c, filter=has_arg)
        @handle('escape', c)
        def _(event):
            event.append_to_arg_count(c)

    for c in '0123456789':
        handle_digit(c)

    @handle('escape', '-', filter=~has_arg)
    def _(event):
        """
        """
        if event._arg is None:
            event.append_to_arg_count('-')

    @handle('-', filter=Condition(lambda: get_app().key_processor.arg == '-'))
    def _(event):
        """
        When '-' is typed again, after exactly '-' has been given as an
        argument, ignore this.
        """
        event.app.key_processor.arg = '-'

    @Condition
    def is_returnable():
        return get_app().current_buffer.is_returnable

    # Meta + Enter: always accept input.
    handle('escape', 'enter', filter=insert_mode & is_returnable)(
        get_by_name('accept-line'))

    # Enter: accept input in single line mode.
    handle('enter', filter=insert_mode & is_returnable & ~is_multiline)(
        get_by_name('accept-line'))

    def character_search(buff, char, count):
        if count < 0:
            match = buff.document.find_backwards(char, in_current_line=True, count=-count)
        else:
            match = buff.document.find(char, in_current_line=True, count=count)

        if match is not None:
            buff.cursor_position += match

    @handle('c-]', Keys.Any)
    def _(event):
        " When Ctl-] + a character is pressed. go to that character. "
        # Also named 'character-search'
        character_search(event.current_buffer, event.data, event.arg)

    @handle('escape', 'c-]', Keys.Any)
    def _(event):
        " Like Ctl-], but backwards. "
        # Also named 'character-search-backward'
        character_search(event.current_buffer, event.data, -event.arg)

    @handle('escape', 'a')
    def _(event):
        " Previous sentence. "
        # TODO:

    @handle('escape', 'e')
    def _(event):
        " Move to end of sentence. "
        # TODO:

    @handle('escape', 't', filter=insert_mode)
    def _(event):
        """
        Swap the last two words before the cursor.
        """
        # TODO

    @handle('escape', '*', filter=insert_mode)
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

    @handle('c-x', 'c-x')
    def _(event):
        """
        Move cursor back and forth between the start and end of the current
        line.
        """
        buffer = event.current_buffer

        if buffer.document.is_cursor_at_the_end_of_line:
            buffer.cursor_position += buffer.document.get_start_of_line_position(after_whitespace=False)
        else:
            buffer.cursor_position += buffer.document.get_end_of_line_position()

    @handle('c-@')  # Control-space or Control-@
    def _(event):
        """
        Start of the selection (if the current buffer is not empty).
        """
        # Take the current cursor position as the start of this selection.
        buff = event.current_buffer
        if buff.text:
            buff.start_selection(selection_type=SelectionType.CHARACTERS)

    @handle('c-g', filter= ~has_selection)
    def _(event):
        """
        Control + G: Cancel completion menu and validation state.
        """
        event.current_buffer.complete_state = None
        event.current_buffer.validation_error = None

    @handle('c-g', filter=has_selection)
    def _(event):
        """
        Cancel selection.
        """
        event.current_buffer.exit_selection()

    @handle('c-w', filter=has_selection)
    @handle('c-x', 'r', 'k', filter=has_selection)
    def _(event):
        """
        Cut selected text.
        """
        data = event.current_buffer.cut_selection()
        event.app.clipboard.set_data(data)

    @handle('escape', 'w', filter=has_selection)
    def _(event):
        """
        Copy selected text.
        """
        data = event.current_buffer.copy_selection()
        event.app.clipboard.set_data(data)

    @handle('escape', 'left')
    def _(event):
        """
        Cursor to start of previous word.
        """
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.find_previous_word_beginning(count=event.arg) or 0

    @handle('escape', 'right')
    def _(event):
        """
        Cursor to start of next word.
        """
        buffer = event.current_buffer
        buffer.cursor_position += buffer.document.find_next_word_beginning(count=event.arg) or \
            buffer.document.get_end_of_document_position()

    @handle('escape', '/', filter=insert_mode)
    def _(event):
        """
        M-/: Complete.
        """
        b = event.current_buffer
        if b.complete_state:
            b.complete_next()
        else:
            b.start_completion(select_first=True)

    @handle('c-c', '>', filter=has_selection)
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

    @handle('c-c', '<', filter=has_selection)
    def _(event):
        """
        Unindent selected text.
        """
        buffer = event.current_buffer

        from_, to = buffer.document.selection_range()
        from_, _ = buffer.document.translate_index_to_position(from_)
        to, _ = buffer.document.translate_index_to_position(to)

        unindent(buffer, from_, to + 1, count=event.arg)

    return ConditionalKeyBindings(key_bindings, emacs_mode)


def load_emacs_search_bindings():
    key_bindings = KeyBindings()
    handle = key_bindings.add
    from . import search

    # NOTE: We don't bind 'Escape' to 'abort_search'. The reason is that we
    #       want Alt+Enter to accept input directly in incremental search mode.
    #       Instead, we have double escape.

    handle('c-r')(search.start_reverse_incremental_search)
    handle('c-s')(search.start_forward_incremental_search)

    handle('c-c')(search.abort_search)
    handle('c-g')(search.abort_search)
    handle('c-r')(search.reverse_incremental_search)
    handle('c-s')(search.forward_incremental_search)
    handle('up')(search.reverse_incremental_search)
    handle('down')(search.forward_incremental_search)
    handle('enter')(search.accept_search)

    # Handling of escape.
    handle('escape', eager=True)(search.accept_search)

    # Like Readline, it's more natural to accept the search when escape has
    # been pressed, however instead the following two bindings could be used
    # instead.
    # #handle('escape', 'escape', eager=True)(search.abort_search)
    # #handle('escape', 'enter', eager=True)(search.accept_search_and_accept_input)

    # If Read-only: also include the following key bindings:

    # '/' and '?' key bindings for searching, just like Vi mode.
    handle('?', filter=is_read_only & ~vi_search_direction_reversed)(search.start_reverse_incremental_search)
    handle('/', filter=is_read_only & ~vi_search_direction_reversed)(search.start_forward_incremental_search)
    handle('?', filter=is_read_only & vi_search_direction_reversed)(search.start_forward_incremental_search)
    handle('/', filter=is_read_only & vi_search_direction_reversed)(search.start_reverse_incremental_search)

    @handle('n', filter=is_read_only)
    def _(event):
        " Jump to next match. "
        event.current_buffer.apply_search(
            event.app.current_search_state,
            include_current_position=False,
            count=event.arg)

    @handle('N', filter=is_read_only)
    def _(event):
        " Jump to previous match. "
        event.current_buffer.apply_search(
            ~event.app.current_search_state,
            include_current_position=False,
            count=event.arg)

    return ConditionalKeyBindings(key_bindings, emacs_mode)
