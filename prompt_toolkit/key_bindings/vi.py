from __future__ import unicode_literals
from ..line import ClipboardData, ClipboardDataType
from ..enums import IncrementalSearchDirection, InputMode
from ..keys import Key

from .basic import basic_bindings
from .utils import create_handle_decorator

__all__ = (
    'vi_bindings',
)


class CursorRegion(object):
    """
    Return struct for functions wrapped in ``change_delete_move_yank_handler``.
    """
    def __init__(self, start, end=0):
        self.start = start
        self.end = end

    def get_sorted(self):
        if self.start < self.end:
            return self.start, self.end
        else:
            return self.end, self.start


def vi_bindings(registry, line):
    """
    Vi extensions.

    # Overview of Readline Vi commands:
    # http://www.catonmat.net/download/bash-vi-editing-mode-cheat-sheet.pdf
    """
    basic_bindings(registry, line)
    handle = create_handle_decorator(registry, line)

    _last_character_find = [None] # (char, backwards) tuple

#    def reset(self):
#        # Remember the last 'F' or 'f' command.
#        self._last_character_find = None # (char, backwards) tuple


    @registry.add_after_handler_callback
    def check_cursor_position(event):
        """
        After every command, make sure that if we are in navigation mode, we
        never put the cursor after the last character of a line. (Unless it's
        an empty line.)
        """
        if (
                event.input_processor.input_mode == InputMode.VI_NAVIGATION and
                line.document.is_cursor_at_the_end_of_line and
                len(line.document.current_line) > 0):
            line.cursor_position -= 1

    @handle(Key.Escape)
    def _(event):
        """
        Escape goes to vi navigation mode.
        """
        event.input_processor.input_mode = InputMode.VI_NAVIGATION

    @handle(Key.Backspace, in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        In navigation-mode, move cursor.
        """
        line.cursor_position += line.document.get_cursor_left_position(count=event.arg)

    #@handle(Key.ControlV, Key.Any, in_mode=InputMode.VI_INSERT)
    #def _(event):
    #    """
    #    Insert a character literally (quoted insert).
    #    """
    #    line.insert_text(event.data, overwrite=False)

    @handle(Key.ControlN)
    def _(event):
        line.complete_next()

        # Switch only to the 'complete' input mode if there really was a
        # completion found.
        if line.complete_state:
            event.input_processor.input_mode = InputMode.COMPLETE

    @handle(Key.ControlP)
    def _(event):
        line.complete_previous()

        # Switch only to the 'complete' input mode if there really was a
        # completion found.
        if line.complete_state:
            event.input_processor.input_mode = InputMode.COMPLETE


    @handle(Key.ControlJ, in_mode=InputMode.VI_NAVIGATION)
    @handle(Key.ControlM, in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        In navigation mode, pressing enter will always return the input.
        """
        line.return_input()

    # ** In navigation mode **

    # List of navigation commands: http://hea-www.harvard.edu/~fine/Tech/vi.html

    @handle('a', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        line.cursor_position += line.document.get_cursor_right_position()
        event.input_processor.input_mode = InputMode.VI_INSERT

    @handle('A', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        line.cursor_position += line.document.get_end_of_line_position()
        event.input_processor.input_mode = InputMode.VI_INSERT

    @handle('C', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        # Change to end of line.
        # Same as 'c$' (which is implemented elsewhere.)
        """
        deleted = line.delete(count=line.document.get_end_of_line_position())
        if deleted:
            data = ClipboardData(deleted)
            line.set_clipboard(data)
        event.input_processor.input_mode = InputMode.VI_INSERT

    @handle('c', 'c', in_mode=InputMode.VI_NAVIGATION)
    @handle('S', in_mode=InputMode.VI_NAVIGATION)
    def _(event): # TODO: implement 'arg'
        """
        Change current line
        """
        # We copy the whole line.
        data = ClipboardData(line.document.current_line, ClipboardDataType.LINES)
        line.set_clipboard(data)

        # But we delete after the whitespace
        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)
        line.delete(count=line.document.get_end_of_line_position())
        event.input_processor.input_mode = InputMode.VI_INSERT

    @handle('D', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        deleted = line.delete(count=line.document.get_end_of_line_position())
        line.set_clipboard(ClipboardData(deleted))

    @handle('d', 'd', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Delete line. (Or the following 'n' lines.)
        """
        # Split string in before/deleted/after text.
        lines = line.document.lines

        before = '\n'.join(lines[:line.document.cursor_position_row])
        deleted = '\n'.join(lines[line.document.cursor_position_row : line.document.cursor_position_row + event.arg])
        after = '\n'.join(lines[line.document.cursor_position_row + event.arg:])

        # Set new text.
        if before and after:
            before = before + '\n'

        line.text = before + after

        # Set cursor position. (At the start of the first 'after' line, after the leading whitespace.)
        line.cursor_position = len(before) + len(after) - len(after.lstrip(' '))

        # Set clipboard data
        line.set_clipboard(ClipboardData(deleted, ClipboardDataType.LINES))

    @handle('G', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Move to the history line n (you may specify the argument n by
        typing it on number keys, for example, 15G)
        """
        line.go_to_history(event.arg - 1)

    @handle('i', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        event.input_processor.input_mode = InputMode.VI_INSERT

    @handle('I', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        event.input_processor.input_mode = InputMode.VI_INSERT
        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

    @handle('J', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        for i in range(event.arg):
            line.join_next_line()

    @handle('n', in_mode=InputMode.VI_NAVIGATION)
    def _(event): # XXX: use `change_delete_move_yank_handler`
        # TODO:
        pass

        # if line.isearch_state:
        #     # Repeat search in the same direction as previous.
        #     line.search_next(line.isearch_state.isearch_direction)

    @handle('N', in_mode=InputMode.VI_NAVIGATION)
    def _(event): # TODO: use `change_delete_move_yank_handler`
        # TODO:
        pass

        #if line.isearch_state:
        #    # Repeat search in the opposite direction as previous.
        #    if line.isearch_state.isearch_direction == IncrementalSearchDirection.FORWARD:
        #        line.search_next(IncrementalSearchDirection.BACKWARD)
        #    else:
        #        line.search_next(IncrementalSearchDirection.FORWARD)

    @handle('p', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Paste after
        """
        for i in range(event.arg):
            line.paste_from_clipboard()

    @handle('P', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Paste before
        """
        for i in range(event.arg):
            line.paste_from_clipboard(before=True)

    @handle('r', Key.Any, in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Replace single character under cursor
        """
        line.insert_text(event.data * event.arg, overwrite=True)

    @handle('R', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Go to 'replace'-mode.
        """
        event.input_processor.input_mode = InputMode.VI_REPLACE

    @handle('s', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Substitute with new text
        (Delete character(s) and go to insert mode.)
        """
        data = ClipboardData(''.join(line.delete() for i in range(event.arg)))
        line.set_clipboard(data)
        event.input_processor.input_mode = InputMode.VI_INSERT

    @handle('u', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        for i in range(event.arg):
            line.undo()

    @handle('v', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        line.open_in_editor()

    @handle('x', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Delete character.
        """
        data = ClipboardData(line.delete(count=event.arg))
        line.set_clipboard(data)

    @handle('X', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        data = line.delete_before_cursor()
        line.set_clipboard(data)

    @handle('y', 'y', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Yank the whole line.
        """
        text = '\n'.join(line.document.lines_from_current[:event.arg])

        data = ClipboardData(text, ClipboardDataType.LINES)
        line.set_clipboard(data)

    @handle('+', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Move to first non whitespace of next line
        """
        line.cursor_position += line.document.get_cursor_down_position(count=event.arg)
        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

    @handle('-', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Move to first non whitespace of previous line
        """
        line.cursor_position += line.document.get_cursor_up_position(count=event.arg)
        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

    @handle('{', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Move to previous blank-line separated section.
        """
        for i in range(event.arg):
            index = line.document.find_previous_matching_line(
                            lambda text: not text or text.isspace())

            if index is not None:
                line.cursor_position += line.document.get_cursor_up_position(count=index)

    @handle('}', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Move to next blank-line separated section.
        """
        for i in range(event.arg):
            index = line.document.find_next_matching_line(
                            lambda text: not text or text.isspace())

            if index is not None:
                line.cursor_position += line.document.get_cursor_down_position(count=index)

    @handle('>', '>', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Indent lines.
        """
        current_line = line.document.cursor_position_row
        line_range = range(current_line, current_line + event.arg)
        line.transform_lines(line_range, lambda l: '    ' + l)

        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

    @handle('<', '<', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Unindent lines.
        """
        current_line = line.document.cursor_position_row
        line_range = range(current_line, current_line + event.arg)

        def transform(text):
            if text.startswith('    '):
                return text[4:]
            else:
                return text.lstrip()

        line.transform_lines(line_range, transform)
        line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

    @handle('O', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Open line above and enter insertion mode
        """
        line.insert_line_above()
        event.input_processor.input_mode = InputMode.VI_INSERT

    @handle('o', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Open line below and enter insertion mode
        """
        line.insert_line_below()
        event.input_processor.input_mode = InputMode.VI_INSERT

    @handle('~', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Reverse case of current character and move cursor forward.
        """
        c = line.document.current_char
        if c is not None and c != '\n':
            c = (c.upper() if c.islower() else c.lower())
            line.insert_text(c, overwrite=True)

    @handle('/', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Search history backward for a command matching string.
        """
        line.incremental_search(IncrementalSearchDirection.FORWARD)
        event.input_processor.input_mode = InputMode.INCREMENTAL_SEARCH

    @handle('?', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Search history forward for a command matching string.
        """
        line.incremental_search(IncrementalSearchDirection.BACKWARD)
        event.input_processor.input_mode = InputMode.INCREMENTAL_SEARCH

    @handle('#', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Go to previous occurence of this word.
        """
        pass

    @handle('*', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Go to next occurence of this word.
        """
        pass

    @handle('(', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        # TODO: go to begin of sentence.
        pass

    @handle(')', in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        # TODO: go to end of sentence.
        pass

    def change_delete_move_yank_handler(*keys, **kw):
        """
        Register a change/delete/move/yank handlers. e.g.  'dw'/'cw'/'w'/'yw'
        The decorated function should return a ``CursorRegion``.
        This decorator will create both the 'change', 'delete' and move variants,
        based on that ``CursorRegion``.
        """
        no_move_handler = kw.pop('no_move_handler', False)

        # TODO: Also do '>' and '<' indent/unindent operators.
        def decorator(func):
            if not no_move_handler:
                @handle(*keys, in_mode=InputMode.VI_NAVIGATION)
                def move(event):
                    """ Create move handler. """
                    region = func(event)
                    line.cursor_position += region.start

            @handle('y', *keys, in_mode=InputMode.VI_NAVIGATION)
            def yank_handler(event):
                """ Create yank handler. """
                region = func(event)

                start, end = region.get_sorted()
                substring = line.text[line.cursor_position + start : line.cursor_position + end]

                if substring:
                    line.set_clipboard(ClipboardData(substring))

            def create(delete_only):
                """ Create delete and change handlers. """
                @handle('cd'[delete_only], *keys, in_mode=InputMode.VI_NAVIGATION)
                @handle('cd'[delete_only], *keys, in_mode=InputMode.VI_NAVIGATION)
                def _(event):
                    region = func(event)
                    deleted = ''

                    if region:
                        start, end = region.get_sorted()

                        # Move to the start of the region.
                        line.cursor_position += start

                        # Delete until end of region.
                        deleted = line.delete(count=end-start)

                    # Set deleted/changed text to clipboard.
                    if deleted:
                        line.set_clipboard(ClipboardData(''.join(deleted)))

                    # Only go back to insert mode in case of 'change'.
                    if not delete_only:
                        event.input_processor.input_mode = InputMode.VI_INSERT

            create(True)
            create(False)
            return func
        return decorator

    @change_delete_move_yank_handler('b') # Move one word or token left.
    @change_delete_move_yank_handler('B') # Move one non-blank word left ((# TODO: difference between 'b' and 'B')
    def key_b(event):
        return CursorRegion(line.document.find_start_of_previous_word(count=event.arg) or 0)

    @change_delete_move_yank_handler('$')
    def key_dollar(event):
        """ 'c$', 'd$' and '$':  Delete/change/move until end of line. """
        return CursorRegion(line.document.get_end_of_line_position())

    @change_delete_move_yank_handler('w') # TODO: difference between 'w' and 'W'
    def key_w(event):
        """ 'cw', 'de', 'w': Delete/change/move one word.  """
        return CursorRegion(line.document.find_next_word_beginning(count=event.arg) or 0)

    @change_delete_move_yank_handler('e') # TODO: difference between 'e' and 'E'
    def key_e(event):
        """ 'ce', 'de', 'e' """
        end = line.document.find_next_word_ending(count=event.arg)
        return CursorRegion(end - 1 if end else 0)

    @change_delete_move_yank_handler('i', 'w', no_move_handler=True)
    def key_iw(event):
        """ ciw and diw """
        # Change inner word: change word under cursor.
        start, end = line.document.find_boundaries_of_current_word()
        return CursorRegion(start, end)

    @change_delete_move_yank_handler('^')
    def key_circumflex(event):
        """ 'c^', 'd^' and '^': Soft start of line, after whitespace. """
        return CursorRegion(line.document.get_start_of_line_position(after_whitespace=True))

    @change_delete_move_yank_handler('0', no_move_handler=True)
    def key_zero(event):
        """
        'c0', 'd0': Hard start of line, before whitespace.
        (The move '0' key is implemented elsewhere, because a '0' could also change the `arg`.)
        """
        return CursorRegion(line.document.get_start_of_line_position(after_whitespace=False))

    def create_ci_ca_handles(ci_start, ci_end, inner):
                # TODO: 'dab', 'dib', (brackets or block) 'daB', 'diB', Braces.
                # TODO: 'dat', 'dit', (tags (like xml)
        """
        Delete/Change string between this start and stop character. But keep these characters.
        This implements all the ci", ci<, ci{, ci(, di", di<, ca", ca<, ... combinations.
        """
        @change_delete_move_yank_handler('ai'[inner], ci_start, no_move_handler=True)
        @change_delete_move_yank_handler('ai'[inner], ci_end, no_move_handler=True)
        def _(event):
            start = line.document.find_backwards(ci_start, in_current_line=True)
            end = line.document.find(ci_end, in_current_line=True)

            if start is not None and end is not None:
                offset = 0 if inner else 1
                return CursorRegion(start + 1 - offset, end + offset)

    for inner in (False, True):
        for ci_start  , ci_end in [ ('"', '"'), ("'", "'"), ("`", "`"),
                            ('[', ']'), ('<', '>'), ('{', '}'), ('(', ')') ]:
            create_ci_ca_handles(ci_start, ci_end, inner)

    @change_delete_move_yank_handler('f', Key.Any)
    def _(event):
        """
        Go to next occurance of character. Typing 'fx' will move the
        cursor to the next occurance of character. 'x'.
        """
        _last_character_find[0] = (event.data, False)
        match = line.document.find(event.data, in_current_line=True, count=event.arg)
        return CursorRegion(match or 0)

    @change_delete_move_yank_handler('F', Key.Any)
    def _(event):
        """
        Go to previous occurance of character. Typing 'Fx' will move the
        cursor to the previous occurance of character. 'x'.
        """
        _last_character_find[0] = (event.data, True)
        return CursorRegion(line.document.find_backwards(event.data, in_current_line=True, count=event.arg) or 0)

    @change_delete_move_yank_handler('t', Key.Any)
    def _(event):
        """
        Move right to the next occurance of c, then one char backward.
        """
        _last_character_find[0] = (event.data, False)
        match = line.document.find(event.data, in_current_line=True, count=event.arg)
        return CursorRegion(match - 1 if match else 0)

    @change_delete_move_yank_handler('T', Key.Any)
    def _(event):
        """
        Move left to the previous occurance of c, then one char forward.
        """
        _last_character_find[0] = (event.data, True)
        match = line.document.find_backwards(event.data, in_current_line=True, count=event.arg)
        return CursorRegion(match + 1 if match else 0)

    def repeat(reverse):
        """
        Create ',' and ';' commands.
        """
        @change_delete_move_yank_handler(',' if reverse else ';')
        def _(event):
            # Repeat the last 'f'/'F'/'t'/'T' command.
            pos = 0

            if _last_character_find[0]:
                char, backwards = _last_character_find[0]

                if reverse:
                    backwards = not backwards

                if backwards:
                    pos = line.document.find_backwards(char, in_current_line=True, count=event.arg)
                else:
                    pos = line.document.find(char, in_current_line=True, count=event.arg)
            return CursorRegion(pos or 0)
    repeat(True)
    repeat(False)

    @change_delete_move_yank_handler('h')
    def _(event):
        """ Implements 'ch', 'dh', 'h': Cursor left. """
        return CursorRegion(line.document.get_cursor_left_position(count=event.arg))

    @change_delete_move_yank_handler('j')
    def _(event):
        """ Implements 'cj', 'dj', 'j', ... Cursor up. """
        return CursorRegion(line.document.get_cursor_down_position(count=event.arg))

    @change_delete_move_yank_handler('k')
    def _(event):
        """ Implements 'ck', 'dk', 'k', ... Cursor up. """
        return CursorRegion(line.document.get_cursor_up_position(count=event.arg))

    @change_delete_move_yank_handler('l')
    @change_delete_move_yank_handler(' ')
    def _(event):
        """ Implements 'cl', 'dl', 'l', 'c ', 'd ', ' '. Cursor right. """
        return CursorRegion(line.document.get_cursor_right_position(count=event.arg))

    @change_delete_move_yank_handler('H')
    def _(event):
        """ Implements 'cH', 'dH', 'H'. """
        # Vi moves to the start of the visible region.
        # cursor position 0 is okay for us.
        return CursorRegion(-len(line.document.text_before_cursor))

    @change_delete_move_yank_handler('L')
    def _(event):
        # Vi moves to the end of the visible region.
        # cursor position 0 is okay for us.
        return CursorRegion(len(line.document.text_after_cursor))

    @change_delete_move_yank_handler('%')
    def _(event):
        """ Implements 'c%', 'd%', '%, 'y%' """
        # Move to the corresponding opening/closing bracket (()'s, []'s and {}'s).
        return CursorRegion(line.document.matching_bracket_position)

    @change_delete_move_yank_handler('|')
    def _(event):
        # Move to the n-th column (you may specify the argument n by typing
        # it on number keys, for example, 20|).
        return CursorRegion(line.document.get_column_cursor_position(event.arg))

    @change_delete_move_yank_handler('g', 'g')
    def _(event):
        """
        Implements 'gg', 'cgg', 'ygg'
        """
        # Move to the top of the input.
        return CursorRegion(line.document.home_position)

    @handle(Key.Any, in_mode=InputMode.VI_NAVIGATION)
    def _(event):
        """
        Always handle numberics in navigation mode as arg.
        """
        if event.data in '123456789' or (event._arg and event.data == '0'):
            event.append_to_arg_count(event.data)
        elif event.data == '0':
            line.cursor_position += line.document.get_start_of_line_position(after_whitespace=False)

    @handle(Key.Any, in_mode=InputMode.VI_REPLACE)
    def _(event):
        """
        Insert data at cursor position.
        """
        line.insert_text(event.data, overwrite=True)
