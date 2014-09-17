from __future__ import unicode_literals
from ..line import ClipboardData, SelectionType
from ..keys import Keys
from ..enums import InputMode, IncrementalSearchDirection

from .basic import basic_bindings
from .utils import create_handle_decorator


def emacs_bindings(registry, cli_ref):
    """
    Some e-macs extensions.
    """
    # Overview of Readline emacs commands:
    # http://www.catonmat.net/download/readline-emacs-editing-mode-cheat-sheet.pdf
    basic_bindings(registry, cli_ref)
    line = cli_ref().line
    search_line = cli_ref().lines['search']
    handle = create_handle_decorator(registry, line)


    @handle(Keys.ControlA, in_mode=InputMode.INSERT)
    @handle(Keys.ControlA, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Start of line.
        """
        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=False)

    @handle(Keys.ControlB, in_mode=InputMode.INSERT)
    @handle(Keys.ControlB, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Character back.
        """
        line.cursor_position += line.document.get_cursor_left_position(count=event.arg)

    @handle(Keys.ControlF, in_mode=InputMode.INSERT)
    @handle(Keys.ControlF, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Character forward.
        """
        line.cursor_position += line.document.get_cursor_right_position(count=event.arg)

    @handle(Keys.ControlN, in_mode=InputMode.INSERT)
    def _(event):
        """
        Next line.
        """
        line.auto_down()

    @handle(Keys.ControlN, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Next line.
        """
        line.cursor_down()

    @handle(Keys.ControlO, in_mode=InputMode.INSERT)
    def _(event):
        """
        Insert newline, but don't move the cursor.
        """
        line.insert_text('\n', move_cursor=False)

    @handle(Keys.ControlP, in_mode=InputMode.INSERT)
    def _(event):
        """
        Previous line.
        """
        line.auto_up()

    @handle(Keys.ControlP, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Previous line.
        """
        line.cursor_up()

    @handle(Keys.ControlQ, Keys.Any, in_mode=InputMode.INSERT)
    def _(event):
        """
        Quoted insert.
        """
        line.insert_text(event.data, overwrite=False)

    @handle(Keys.ControlY, in_mode=InputMode.INSERT)
    def _(event):
        """
        Paste before cursor.
        """
        line.paste_from_clipboard(before=True)

    @handle(Keys.ControlUnderscore, save_before=False, in_mode=InputMode.INSERT)
    def _(event):
        """
        Undo.
        """
        line.undo()

    def handle_digit(c):
        """
        Handle Alt + digit in the `meta_digit` method.
        """
        @handle(Keys.Escape, c, in_mode=InputMode.INSERT)
        def _(event):
            event.append_to_arg_count(c)

    for c in '0123456789':
        handle_digit(c)

    @handle(Keys.Escape, '-', in_mode=InputMode.INSERT)
    def _(event):
        """
        """
        if event._arg == None:
            event.append_to_arg_count('-')

    @handle(Keys.Escape, Keys.ControlJ, in_mode=InputMode.INSERT)
    @handle(Keys.Escape, Keys.ControlM, in_mode=InputMode.INSERT)
    @handle(Keys.Escape, Keys.ControlJ, in_mode=InputMode.COMPLETE)
    @handle(Keys.Escape, Keys.ControlM, in_mode=InputMode.COMPLETE)
    @handle(Keys.Escape, Keys.ControlJ, in_mode=InputMode.INCREMENTAL_SEARCH)
    @handle(Keys.Escape, Keys.ControlM, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        """
        Meta + Newline: always accept input.
        """
        line.return_input()

    @handle(Keys.ControlSquareClose, Keys.Any, in_mode=InputMode.INSERT)
    @handle(Keys.ControlSquareClose, Keys.Any, in_mode=InputMode.SELECTION)
    def _(event):
        """
        When Ctl-] + a character is pressed. go to that character.
        """
        match = line.document.find(event.data, in_current_line=True, count=(event.arg))
        if match is not None:
            line.cursor_position += match

    @handle(Keys.Escape, Keys.Backspace, in_mode=InputMode.INSERT)
    def _(event):
        """
        Delete word backwards.
        """
        pos = line.document.find_start_of_previous_word(count=event.arg)
        if pos:
            deleted = line.delete_before_cursor(count=-pos)
            line.set_clipboard(ClipboardData(deleted))

    @handle(Keys.Escape, 'a', in_mode=InputMode.INSERT)
    def _(event):
        """
        Previous sentence.
        """
        # TODO:
        pass

    @handle(Keys.Escape, 'c', in_mode=InputMode.INSERT)
    def _(event):
        """
        Capitalize the current (or following) word.
        """
        for i in range(event.arg):
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.title(), overwrite=True)

    @handle(Keys.Escape, 'e', in_mode=InputMode.INSERT)
    def _(event):
        """ Move to end of sentence. """
        # TODO:
        pass

    @handle(Keys.Escape, 'f', in_mode=InputMode.INSERT)
    @handle(Keys.Escape, 'f', in_mode=InputMode.SELECTION)
    def _(event):
        """
        Cursor to end of next word.
        """
        pos = line.document.find_next_word_ending(count=event.arg)
        if pos:
            line.cursor_position += pos

    @handle(Keys.Escape, 'b', in_mode=InputMode.INSERT)
    @handle(Keys.Escape, 'b', in_mode=InputMode.SELECTION)
    def _(event):
        """
        Cursor to start of previous word.
        """
        pos = line.document.find_previous_word_beginning(count=event.arg)
        if pos:
            line.cursor_position += pos

    @handle(Keys.Escape, 'l', in_mode=InputMode.INSERT)
    def _(event):
        """
        Lowercase the current (or following) word.
        """
        for i in range(event.arg): # XXX: not DRY: see meta_c and meta_u!!
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.lower(), overwrite=True)

    @handle(Keys.Escape, 't', in_mode=InputMode.INSERT)
    def _(event):
        """
        Swap the last two words before the cursor.
        """
        # TODO

    @handle(Keys.Escape, 'u', in_mode=InputMode.INSERT)
    def _(event):
        """
        Uppercase the current (or following) word.
        """
        for i in range(event.arg):
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.upper(), overwrite=True)

    @handle(Keys.Escape, '.', in_mode=InputMode.INSERT)
    def _(event):
        """
        Rotate through the last word (white-space delimited) of the previous lines in history.
        """
        # TODO

    @handle(Keys.Escape, '\\', in_mode=InputMode.INSERT)
    def _(event):
        """
        Delete all spaces and tabs around point.
        (delete-horizontal-space)
        """

    @handle(Keys.Escape, '*', in_mode=InputMode.INSERT)
    def _(event):
        """
        `meta-*`: Insert all possible completions of the preceding text.
        """

    @handle(Keys.ControlX, Keys.ControlE, in_mode=InputMode.INSERT)
    def _(event):
        """
        Open editor.
        """
        line.open_in_editor()

    @handle(Keys.ControlX, Keys.ControlU, save_before=False, in_mode=InputMode.INSERT)
    def _(event):
        line.undo()

    @handle(Keys.ControlX, Keys.ControlX, in_mode=InputMode.INSERT)
    @handle(Keys.ControlX, Keys.ControlX, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Move cursor back and forth between the start and end of the current
        line.
        """
        if line.document.current_char == '\n':
            line.cursor_position += line.document.get_start_of_line_position(after_whitespace=False)
        else:
            line.cursor_position += line.document.get_end_of_line_position()

    @handle(Keys.Escape, in_mode=InputMode.COMPLETE)
    def _(event):
        """ Pressing escape in complete mode, goes back to emacs insert mode. """
        event.input_processor.pop_input_mode()

    @handle(Keys.ControlSpace, in_mode=InputMode.INSERT)
    @handle(Keys.ControlSpace, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Start of the selection.
        """
        # Take the current cursor position as the start of this selection.
        line.start_selection(selection_type=SelectionType.CHARACTERS)

        if event.input_processor.input_mode != InputMode.SELECTION:
            event.input_processor.push_input_mode(InputMode.SELECTION)

    @handle(Keys.ControlG, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Cancel selection.
        """
        event.input_processor.pop_input_mode()
        line.exit_selection()

    @handle(Keys.ControlW, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Cut selected text.
        """
        deleted = line.cut_selection()
        line.set_clipboard(ClipboardData(deleted))
        event.input_processor.pop_input_mode()

    @handle(Keys.Escape, 'w', in_mode=InputMode.SELECTION)
    def _(event):
        """
        Copy selected text.
        """
        text = line.copy_selection()
        line.set_clipboard(ClipboardData(text))
        event.input_processor.pop_input_mode()

    @handle(Keys.Escape, '<', in_mode=InputMode.INSERT)
    def _(event):
        """
        Move to the first line in the history.
        """
        line.go_to_history(0)

    @handle(Keys.Escape, '>', in_mode=InputMode.INSERT)
    def _(event):
        """
        Move to the end of the input history.
        This is the line we are editing.
        """
        line.go_to_history(len(line._working_lines) - 1)

    @handle(Keys.ControlH, in_mode=InputMode.INCREMENTAL_SEARCH)
    @handle(Keys.Backspace, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        search_line.delete_before_cursor()
        line.set_search_text(search_line.text)

    @handle(Keys.Any, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        """
        Insert isearch string.
        """
        search_line.insert_text(event.data)
        line.set_search_text(search_line.text)

    @handle(Keys.ControlG, in_mode=InputMode.INCREMENTAL_SEARCH)
    # NOTE: the reason for not binding Escape to this one, is that we want
    #       Alt+Enter to accept input directly in incremental search mode.
    def _(event):
        """
        Abort an incremental search and restore the original line.
        """
        line.exit_isearch(restore_original_line=True)
        event.input_processor.pop_input_mode()
        search_line.reset()

    @handle(Keys.ControlJ, in_mode=InputMode.INCREMENTAL_SEARCH)
    @handle(Keys.ControlM, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        """
        When enter pressed in isearch, quit isearch mode. (Multiline
        isearch would be too complicated.)
        """
        search_line.reset()
        line.exit_isearch()
        event.input_processor.pop_input_mode()

    @handle(Keys.ControlR, in_mode=InputMode.INSERT)
    @handle(Keys.ControlR, in_mode=InputMode.INCREMENTAL_SEARCH)
    @handle(Keys.Up, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        line.incremental_search(IncrementalSearchDirection.BACKWARD)

        if event.input_processor.input_mode != InputMode.INCREMENTAL_SEARCH:
            event.input_processor.push_input_mode(InputMode.INCREMENTAL_SEARCH)

    @handle(Keys.ControlS, in_mode=InputMode.INSERT)
    @handle(Keys.ControlS, in_mode=InputMode.INCREMENTAL_SEARCH)
    @handle(Keys.Down, in_mode=InputMode.INCREMENTAL_SEARCH)
    def _(event):
        line.incremental_search(IncrementalSearchDirection.FORWARD)

        if event.input_processor.input_mode != InputMode.INCREMENTAL_SEARCH:
            event.input_processor.push_input_mode(InputMode.INCREMENTAL_SEARCH)

    @handle(Keys.Escape, Keys.Left, in_mode=InputMode.INSERT)
    @handle(Keys.Escape, Keys.Left, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Cursor to start of previous word.
        """
        line.cursor_position += line.document.find_previous_word_beginning(count=event.arg) or 0

    @handle(Keys.Escape, Keys.Right, in_mode=InputMode.INSERT)
    @handle(Keys.Escape, Keys.Right, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Cursor to start of next word.
        """
        line.cursor_position += line.document.find_next_word_beginning(count=event.arg) or 0

    @handle(Keys.Escape, '/', in_mode=InputMode.INSERT)
    @handle(Keys.Escape, '/', in_mode=InputMode.COMPLETE)
    def _(event):
        """
        M-/: Complete.
        """
        line.complete_next()

        # Switch only to the 'complete' input mode if there really was a completion found.
        if line.complete_state and event.input_processor.input_mode != InputMode.COMPLETE:
            event.input_processor.push_input_mode(InputMode.COMPLETE)
