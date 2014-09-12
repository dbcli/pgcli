from __future__ import unicode_literals
from ..line import ClipboardData, SelectionType
from ..keys import Keys
from ..enums import InputMode

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
    handle = create_handle_decorator(registry, line)

    @handle(Keys.ControlN)
    def _(event):
        line.auto_down()

    @handle(Keys.ControlO)
    def _(event):
        """
        Insert newline, but don't move the cursor.
        """
        line.insert_text('\n', move_cursor=False)

    @handle(Keys.ControlP)
    def _(event):
        line.auto_up()

    @handle(Keys.ControlQ, Keys.Any, in_mode=InputMode.INSERT)
    def _(event):
        """
        Quoted insert.
        """
        line.insert_text(event.data, overwrite=False)

    @handle(Keys.ControlY)
    def _(event):
        """
        Paste before cursor.
        """
        line.paste_from_clipboard(before=True)

    @handle(Keys.ControlUnderscore, save_before=False)
    def _(event):
        """
        Undo.
        """
        line.undo()

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
        if event._arg == None:
            event.append_to_arg_count('-')

    @handle(Keys.Escape, Keys.ControlJ)
    @handle(Keys.Escape, Keys.ControlM)
    def _(event):
        """
        Meta + Newline: always accept input.
        """
        line.return_input()

    @handle(Keys.ControlSquareClose, Keys.Any)
    def _(event):
        """
        When Ctl-] + a character is pressed. go to that character.
        """
        match = line.document.find(event.data, in_current_line=True, count=(event.arg))
        if match is not None:
            line.cursor_position += match

    @handle(Keys.Escape, Keys.Backspace)
    def _(event):
        """
        Delete word backwards.
        """
        pos = line.document.find_start_of_previous_word(count=event.arg)
        if pos:
            deleted = line.delete_before_cursor(count=-pos)
            line.set_clipboard(ClipboardData(deleted))

    @handle(Keys.Escape, 'a')
    def _(event):
        """
        Previous sentence.
        """
        # TODO:
        pass

    @handle(Keys.Escape, 'c')
    def _(event):
        """
        Capitalize the current (or following) word.
        """
        for i in range(event.arg):
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.title(), overwrite=True)

    @handle(Keys.Escape, 'e')
    def _(event):
        """ Move to end of sentence. """
        # TODO:
        pass

    @handle(Keys.Escape, 'f')
    def _(event):
        """
        Cursor to end of next word.
        """
        pos = line.document.find_next_word_ending(count=event.arg)
        if pos:
            line.cursor_position += pos

    @handle(Keys.Escape, 'b')
    def _(event):
        """
        Cursor to start of previous word.
        """
        pos = line.document.find_previous_word_beginning(count=event.arg)
        if pos:
            line.cursor_position += pos

    @handle(Keys.Escape, 'b')
    def _(event):
        """
        Delete the Word after the cursor. (Delete until end of word.)
        """
        pos = line.document.find_next_word_ending()
        data = ClipboardData(line.delete(pos))
        line.set_clipboard(data)

    @handle(Keys.Escape, 'l')
    def _(event):
        """
        Lowercase the current (or following) word.
        """
        for i in range(event.arg): # XXX: not DRY: see meta_c and meta_u!!
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.lower(), overwrite=True)

    @handle(Keys.Escape, 't')
    def _(event):
        """
        Swap the last two words before the cursor.
        """
        # TODO

    @handle(Keys.Escape, 'u')
    def _(event):
        """
        Uppercase the current (or following) word.
        """
        for i in range(event.arg):
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.upper(), overwrite=True)

    @handle(Keys.Escape, 'w')
    def _(event):
        """
        Copy current region.
        """
        # TODO

    @handle(Keys.Escape, '.')
    def _(event):
        """
        Rotate through the last word (white-space delimited) of the previous lines in history.
        """
        # TODO

    @handle(Keys.Escape, '\\')
    def _(event):
        """
        Delete all spaces and tabs around point.
        (delete-horizontal-space)
        """

    @handle(Keys.Escape, '*')
    def _(event):
        """
        `meta-*`: Insert all possible completions of the preceding text.
        """

    @handle(Keys.ControlX, Keys.ControlE)
    def _(event):
        """
        Open editor.
        """
        line.open_in_editor()

    @handle(Keys.ControlX, Keys.ControlU, save_before=False)
    def _(event):
        line.undo()

    @handle(Keys.ControlX, Keys.ControlX)
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

    @handle(Keys.ControlSpace)
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
