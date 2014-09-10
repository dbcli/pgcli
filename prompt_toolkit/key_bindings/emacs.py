from __future__ import unicode_literals
from ..line import ClipboardData, SelectionType
from ..keys import Key
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

    @handle(Key.ControlN)
    def _(event):
        line.auto_down()

    @handle(Key.ControlO)
    def _(event):
        """
        Insert newline, but don't move the cursor.
        """
        line.insert_text('\n', move_cursor=False)

    @handle(Key.ControlP)
    def _(event):
        line.auto_up()

#    @handle(Key.ControlW)
#    def _(event):
#        # TODO: if selection: cut current region.
#        # otherwise, cut word before cursor:
#        super(EmacsInputStreamHandler, self).ctrl_w()

    @handle(Key.ControlY)
    def _(event):
        """
        Paste before cursor.
        """
        line.paste_from_clipboard(before=True)

    @handle(Key.ControlSpace)
    def _(event):
        """
        Select region.
        """
        # TODO
        pass

    @handle(Key.ControlUnderscore, save_before=False)
    def _(event):
        """
        Undo.
        """
        line.undo()

    @handle(Key.Escape, Key.Any)
    def _(event):
        """
        Handle Alt + digit in the `meta_digit` method.
        """
        if event.data in '0123456789' or (event.data == '-' and line.input_arg == None):
            event.append_to_arg_count(event.data)

    @handle(Key.Escape, Key.ControlJ)
    @handle(Key.Escape, Key.ControlM)
    def _(event):
        """
        Meta + Newline: always accept input.
        """
        line.return_input()

    @handle(Key.ControlSquareClose, Key.Any)
    def _(event):
        """
        When Ctl-] + a character is pressed. go to that character.
        """
        match = line.document.find(event.data, in_current_line=True, count=(event.arg))
        if match is not None:
            line.cursor_position += match

    @handle(Key.Escape, Key.Backspace)
    def _(event):
        """
        Delete word backwards.
        """
        pos = line.document.find_start_of_previous_word(count=event.arg)
        if pos:
            deleted = line.delete_before_cursor(count=-pos)
            line.set_clipboard(ClipboardData(deleted))

    @handle(Key.Escape, 'a')
    def _(event):
        """
        Previous sentence.
        """
        # TODO:
        pass

    @handle(Key.Escape, 'c')
    def _(event):
        """
        Capitalize the current (or following) word.
        """
        for i in range(event.arg):
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.title(), overwrite=True)

    @handle(Key.Escape, 'e')
    def _(event):
        """ Move to end of sentence. """
        # TODO:
        pass

    @handle(Key.Escape, 'f')
    def _(event):
        """
        Cursor to end of next word.
        """
        pos = line.document.find_next_word_ending(count=event.arg)
        if pos:
            line.cursor_position += pos

    @handle(Key.Escape, 'b')
    def _(event):
        """
        Cursor to start of previous word.
        """
        pos = line.document.find_previous_word_beginning(count=event.arg)
        if pos:
            line.cursor_position += pos

    @handle(Key.Escape, 'b')
    def _(event):
        """
        Delete the Word after the cursor. (Delete until end of word.)
        """
        pos = line.document.find_next_word_ending()
        data = ClipboardData(line.delete(pos))
        line.set_clipboard(data)

    @handle(Key.Escape, 'l')
    def _(event):
        """
        Lowercase the current (or following) word.
        """
        for i in range(event.arg): # XXX: not DRY: see meta_c and meta_u!!
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.lower(), overwrite=True)

    @handle(Key.Escape, 't')
    def _(event):
        """
        Swap the last two words before the cursor.
        """
        # TODO

    @handle(Key.Escape, 'u')
    def _(event):
        """
        Uppercase the current (or following) word.
        """
        for i in range(event.arg):
            pos = line.document.find_next_word_ending()
            words = line.document.text_after_cursor[:pos]
            line.insert_text(words.upper(), overwrite=True)

    @handle(Key.Escape, 'w')
    def _(event):
        """
        Copy current region.
        """
        # TODO

    @handle(Key.Escape, '.')
    def _(event):
        """
        Rotate through the last word (white-space delimited) of the previous lines in history.
        """
        # TODO

    @handle(Key.Escape, '\\')
    def _(event):
        """
        Delete all spaces and tabs around point.
        (delete-horizontal-space)
        """

    @handle(Key.Escape, '*')
    def _(event):
        """
        `meta-*`: Insert all possible completions of the preceding text.
        """

    @handle(Key.ControlX, Key.ControlE)
    def _(event):
        """
        Open editor.
        """
        line.open_in_editor()

    @handle(Key.ControlX, Key.ControlU, save_before=False)
    def _(event):
        line.undo()

    @handle(Key.ControlX, Key.ControlX)
    def _(event):
        """
        Move cursor back and forth between the start and end of the current
        line.
        """
        if line.document.current_char == '\n':
            line.cursor_position += line.document.get_start_of_line_position(after_whitespace=False)
        else:
            line.cursor_position += line.document.get_end_of_line_position()

    @handle(Key.Escape, in_mode=InputMode.COMPLETE)
    def _(event):
        """ Pressing escape in complete mode, goes back to emacs insert mode. """
        event.input_processor.pop_input_mode()

    @handle(Key.ControlSpace)
    @handle(Key.ControlSpace, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Start of the selection.
        """
        # Take the current cursor position as the start of this selection.
        line.start_selection(selection_type=SelectionType.CHARACTERS)

        if event.input_processor.input_mode != InputMode.SELECTION:
            event.input_processor.push_input_mode(InputMode.SELECTION)

    @handle(Key.ControlW, in_mode=InputMode.SELECTION)
    def _(event):
        """
        Cut selected text.
        """
        deleted = line.cut_selection()
        line.set_clipboard(ClipboardData(deleted))

    @handle(Key.Escape, 'w', in_mode=InputMode.SELECTION)
    def _(event):
        """
        Copy selected text.
        """
        text = line.copy_selection()
        line.set_clipboard(ClipboardData(text))
