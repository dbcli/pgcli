# *** encoding: utf-8 ***
"""
An :class:`~.InputStreamHandler` receives callbacks for the keystrokes parsed
from the input in the :class:`~prompt_toolkit.inputstream.InputStream`
instance.

The `InputStreamHandler` will according to the implemented keybindings apply
the correct manipulations on the :class:`~prompt_toolkit.line.Line` object.

This module implements Vi and Emacs keybindings.
"""
from __future__ import unicode_literals
from .line import ClipboardData, ClipboardDataType
from .enums import IncrementalSearchDirection, LineMode

__all__ = (
    'InputStreamHandler',
    'EmacsInputStreamHandler',
    'ViInputStreamHandler'
)


class InputStreamHandler(object):
    """
    This is the base class for :class:`~.EmacsInputStreamHandler` and
    :class:`~.ViInputStreamHandler`. It implements the common keybindings.

    :attr line: :class:`~prompt_toolkit.line.Line` class.
    """
    def __init__(self, line):
        self.line = line
        self.reset()

    def reset(self):
        #: True when the user pressed on the 'tab' key.
        self._second_tab = False

        #: The name of the last previous public function call.
        self._last_call = None

        self._arg_count = None

    def get_arg_count(self):
        """
        Return 'arg' count. For command repeats.
        Calling this function will also reset the arg count.
        """
        value = self._arg_count
        self._arg_count = None
        self.line.set_arg_prompt('')
        return value or 1

    def set_arg_count(self, value):
        self._arg_count = value

        # Set argument prompt
        if value:
            self.line.set_arg_prompt(value)
        else:
            self.line.set_arg_prompt('')

    def __call__(self, name, *a):
        if name != 'ctrl_i':
            self._second_tab = False

        # Call actual handler
        method = getattr(self, name, None)
        if method:
            # First, safe current state to undo stack
            if self._needs_to_save(name):
                self.line.save_to_undo_stack()

            method(*a)

        # Keep track of what the last called method was.
        if not name.startswith('_'):
            self._last_call = name

    def _needs_to_save(self, current_method):
        """
        `True` when we need to save the line of the line before calling this method.
        """
        # But don't create an entry in the history buffer for every single typed
        # character. (Undo should undo multiple typed characters at once.)
        return not (current_method == 'insert_char' and self._last_call == 'insert_char')

    def home(self):
        self.line.cursor_position += self.line.document.home_position

    def end(self):
        self.line.cursor_position += self.line.document.end_position

    # CTRL keys.

    def ctrl_a(self):
        self.line.cursor_position += self.line.document.get_start_of_line_position(after_whitespace=False)

    def ctrl_b(self):
        self.line.cursor_position += self.line.document.get_cursor_left_position(count=self.get_arg_count())

    def ctrl_c(self):
        self.line.abort()

    def ctrl_d(self):
        # When there is text, act as delete, otherwise call exit.
        if self.line.text:
            self.line.delete()
        else:
            self.line.exit()

    def ctrl_e(self):
        self.line.cursor_position += self.line.document.get_end_of_line_position()

    def ctrl_f(self):
        self.line.cursor_position += self.line.document.get_cursor_right_position(count=self.get_arg_count())

    def ctrl_g(self):
        """ Abort an incremental search and restore the original line """
        self.line.exit_isearch(restore_original_line=True)

    def ctrl_h(self):
        self.line.delete_before_cursor()

    def ctrl_i(self):
        r""" Ctrl-I is identical to "\t" """
        self.tab()

    def ctrl_j(self):
        """ Newline."""
        self.enter()

    def ctrl_k(self):
        deleted = self.line.delete(count=self.line.document.get_end_of_line_position())
        self.line.set_clipboard(ClipboardData(deleted))

    def ctrl_l(self):
        self.line.clear()

    def ctrl_m(self):
        """ Carriage return """
        # Alias for newline.
        self.ctrl_j()

    def ctrl_n(self):
        self.line.history_forward()

    def ctrl_o(self):
        pass

    def ctrl_p(self):
        self.line.history_backward()

    def ctrl_q(self):
        pass

    def ctrl_r(self):
        self.line.reverse_search()

    def ctrl_s(self):
        self.line.forward_search()

    def ctrl_t(self):
        self.line.swap_characters_before_cursor()

    def ctrl_u(self):
        """
        Clears the line before the cursor position. If you are at the end of
        the line, clears the entire line.
        """
        deleted = self.line.delete_before_cursor(count=-self.line.document.get_start_of_line_position())
        self.line.set_clipboard(ClipboardData(deleted))

    def ctrl_v(self):
        pass

    def ctrl_w(self):
        """
        Delete the word before the cursor.
        """
        pos = self.line.document.find_start_of_previous_word(count=self.get_arg_count())
        if pos:
            deleted = self.line.delete_before_cursor(count=-pos)
            self.line.set_clipboard(ClipboardData(deleted))

    def ctrl_x(self):
        pass

    def ctrl_y(self):
        # Pastes the clipboard content.
        self.line.paste_from_clipboard()

    def ctrl_z(self):
        pass

    def page_up(self):
        if self.line.mode == LineMode.COMPLETE:
            self.line.complete_previous(5)
        else:
            self.line.history_backward()

    def page_down(self):
        if self.line.mode == LineMode.COMPLETE:
            self.line.complete_next(5)
        else:
            self.line.history_forward()

    def arrow_left(self):
        self.line.cursor_position += self.line.document.get_cursor_left_position(count=self.get_arg_count())

    def arrow_right(self):
        self.line.cursor_position += self.line.document.get_cursor_right_position(count=self.get_arg_count())

    def arrow_up(self):
        self.line.auto_up(count=self.get_arg_count())

    def arrow_down(self):
        self.line.auto_down(count=self.get_arg_count())

    def backspace(self):
        self.line.delete_before_cursor(count=self.get_arg_count())

    def delete(self):
        self.line.delete(count=self.get_arg_count())

    def shift_delete(self):
        self.delete()

    def tab(self):
        """
        Autocomplete.
        """
        self.do_traditional_complete()

    def do_traditional_complete(self):
        """
        Traditional tab-completion, where the first tab completes the common
        suffix and the second tab lists all the completions.
        """
        if self._second_tab:
            self.line.list_completions()
            self._second_tab = False
        else:
            self._second_tab = not self.line.complete_common()

    def insert_char(self, data):
        """ Insert data at cursor position.  """
        assert len(data) == 1
        self.line.insert_text(data * self.get_arg_count())

    def enter(self):
        if self.line.mode == LineMode.INCREMENTAL_SEARCH:
            # When enter pressed in isearch, quit isearch mode. (Multiline
            # isearch would be too complicated.)
            self.line.exit_isearch()

        elif self.line.is_multiline:
            self.line.newline()
        else:
            self.line.return_input()

    def meta_arrow_left(self):
        """ Cursor to start of previous word. """
        self.line.cursor_position += (self.line.document.find_previous_word_beginning(count=self.get_arg_count()) or 0)

    def meta_arrow_right(self):
        """ Cursor to start of next word. """
        self.line.cursor_position += (self.line.document.find_next_word_beginning(count=self.get_arg_count()) or 0)


class EmacsInputStreamHandler(InputStreamHandler):
    """
    Some e-macs extensions.
    """
    # Overview of Readline emacs commands:
    # http://www.catonmat.net/download/readline-emacs-editing-mode-cheat-sheet.pdf

    def reset(self):
        super(EmacsInputStreamHandler, self).reset()
        self._escape_pressed = False
        self._ctrl_x_pressed = False
        self._ctrl_square_close_pressed = False

    def escape(self):
        # Escape is the same as the 'meta-' prefix.
        self._escape_pressed = True

    def ctrl_n(self):
        self.line.auto_down()

    def ctrl_o(self):
        """ Insert newline, but don't move the cursor. """
        self.line.insert_text('\n', move_cursor=False)

    def ctrl_p(self):
        self.line.auto_up()

    def ctrl_w(self):
        # TODO: if selection: cut current region.
        # otherwise, cut word before cursor:
        super(EmacsInputStreamHandler, self).ctrl_w()

    def ctrl_x(self):
        self._ctrl_x_pressed = True

    def ctrl_y(self):
        """ Paste before cursor. """
        self.line.paste_from_clipboard(before=True)

    def ctrl_square_close(self):
        """ Ctrl+], followed by character. Go to character. """
        self._ctrl_square_close_pressed = True

    def __call__(self, name, *a):
                # TODO: implement these states (meta-prefix and  ctrl_x)
                #       in separate InputStreamHandler classes.If a method, like (ctl_x)
                #       is called and returns an object. That should become the
                #       new handler.

        # When Ctl-] + a character is pressed. go to that character.
        if self._ctrl_square_close_pressed:
            if name == 'insert_char':
                match = self.line.document.find(a[0], in_current_line=True, count=(self.get_arg_count()))
                if match is not None:
                    self.line.cursor_position += match
            self._ctrl_square_close_pressed= False
            return

        # When escape was pressed, call the `meta_`-function instead.
        # (This is emacs-mode behaviour. The meta-prefix is equal to the escape
        # key, and in VI mode, that's used to go from insert to navigation mode.)
        if self._escape_pressed:
            if name == 'insert_char':
                # Handle Alt + digit in the `meta_digit` method.
                if a[0] in '0123456789' or (a[0] == '-' and self._arg_count == None):
                    self.set_arg_count(_arg_count_append(self._arg_count, a[0]))
                    self._escape_pressed = False
                    return

                # Handle Alt + char in their respective `meta_X` method.
                elif ord(a[0]) < 128:
                        # The odr<128 test is just to make sure that we only create
                        # ASCII names. alt-§ otherwise crashes in Python27
                    name = 'meta_' + a[0]
                    a = []
            else:
                name = 'meta_' + name
            self._escape_pressed = False

        # If Ctrl-x was pressed. Prepend ctrl_x prefix to hander name.
        if self._ctrl_x_pressed:
            name = 'ctrl_x_%s' % name

        super(EmacsInputStreamHandler, self).__call__(name, *a)

        # Reset ctrl_x state.
        if name != 'ctrl_x':
            self._ctrl_x_pressed = False

    def _needs_to_save(self, current_method):
        # Don't save the current state at the undo-stack for following methods.
        if current_method in ('ctrl_x', 'ctrl_x_ctrl_u', 'ctrl_underscore'):
            return False

        return super(EmacsInputStreamHandler, self)._needs_to_save(current_method)

    def meta_ctrl_j(self):
        """ ALT + Newline """
        # Alias for meta_enter
        self.meta_enter()

    def meta_ctrl_m(self):
        """ ALT + Carriage return """
        # Alias for meta_enter
        self.meta_enter()

    def meta_enter(self):
        """ Alt + Enter. Should always accept input. """
        self.line.return_input()

    def meta_backspace(self):
        """ Delete word backwards. """
        pos = self.line.document.find_start_of_previous_word(count=self.get_arg_count())
        if pos:
            deleted = self.line.delete_before_cursor(count=-pos)
            self.line.set_clipboard(ClipboardData(deleted))

    def meta_a(self):
        """
        Previous sentence.
        """
        # TODO:
        pass

    def meta_c(self):
        """
        Capitalize the current (or following) word.
        """
        for i in range(self.get_arg_count()):
            pos = self.line.document.find_next_word_ending()
            words = self.line.document.text_after_cursor[:pos]
            self.line.insert_text(words.title(), overwrite=True)

    def meta_e(self):
        """ Move to end of sentence. """
        # TODO:
        pass

    def meta_f(self):
        """
        Cursor to end of next word.
        """
        pos = self.line.document.find_next_word_ending(count=self.get_arg_count())
        if pos:
            self.line.cursor_position += pos

    def meta_b(self):
        """ Cursor to start of previous word. """
        pos = self.line.document.find_previous_word_beginning(count=self.get_arg_count())
        if pos:
            self.line.cursor_position += pos

    def meta_d(self):
        """
        Delete the Word after the cursor. (Delete until end of word.)
        """
        pos = self.line.document.find_next_word_ending()
        data = ClipboardData(self.line.delete(pos))
        self.line.set_clipboard(data)

    def meta_l(self):
        """
        Lowercase the current (or following) word.
        """
        for i in range(self.get_arg_count()): # XXX: not DRY: see meta_c and meta_u!!
            pos = self.line.document.find_next_word_ending()
            words = self.line.document.text_after_cursor[:pos]
            self.line.insert_text(words.lower(), overwrite=True)

    def meta_t(self):
        """
        Swap the last two words before the cursor.
        """
        # TODO

    def meta_u(self):
        """
        Uppercase the current (or following) word.
        """
        for i in range(self.get_arg_count()):
            pos = self.line.document.find_next_word_ending()
            words = self.line.document.text_after_cursor[:pos]
            self.line.insert_text(words.upper(), overwrite=True)

    def meta_w(self):
        """
        Copy current region.
        """
        # TODO

    def meta_dot(self):
        """
        Rotate through the last word (white-space delimited) of the previous lines in history.
        """
        # TODO

    def ctrl_space(self):
        """
        Select region.
        """
        # TODO
        pass

    def ctrl_underscore(self):
        """
        Undo.
        """
        self.line.undo()

    def meta_backslash(self):
        """
        Delete all spaces and tabs around point.
        (delete-horizontal-space)
        """

    def meta_star(self):
        """
        `meta-*`: Insert all possible completions of the preceding text.
        """

    def ctrl_x_ctrl_e(self):
        """
        Open editor.
        """
        self.line.open_in_editor()

    def ctrl_x_ctrl_u(self):
        self.line.undo()

    def ctrl_x_ctrl_x(self):
        """
        Move cursor back and forth between the start and end of the current
        line.
        """
        if self.line.document.current_char == '\n':
            self.line.cursor_position += self.line.document.get_start_of_line_position(after_whitespace=False)
        else:
            self.line.cursor_position += self.line.document.get_end_of_line_position()


class ViMode(object):
    NAVIGATION = 'navigation'
    INSERT = 'insert'
    REPLACE = 'replace'

    # TODO: Not supported. But maybe for some day...
    VISUAL = 'visual'
    VISUAL_LINE = 'visual-line'
    VISUAL_BLOCK = 'visual-block'


class ViInputStreamHandler(InputStreamHandler):
    """
    Vi extensions.

    # Overview of Readline Vi commands:
    # http://www.catonmat.net/download/bash-vi-editing-mode-cheat-sheet.pdf
    """
    def reset(self):
        super(ViInputStreamHandler, self).reset()
        self._vi_mode = ViMode.INSERT
        self._all_navigation_handles = self._get_navigation_mode_handles()

        # Hook for several actions in navigation mode which require an
        # additional key to be typed before they execute.
        self._one_character_callback = None

        # Remember the last 'F' or 'f' command.
        self._last_character_find = None # (char, backwards) tuple

        # Macros.
        self._macro_recording_register = None
        self._macro_recording_calls = [] # List of currently recording commands.
        self._macros = {} # Maps macro char to commands.
        self._playing_macro = False

    @property
    def is_recording_macro(self):
        """ True when we are currently recording a macro. """
        return bool(self._macro_recording_register)

    def __call__(self, name, *a):
        # Save in macro, if we are recording.
        if self._macro_recording_register:
            self._macro_recording_calls.append( (name,) + a)

        super(ViInputStreamHandler, self).__call__(name, *a)

        # After every command, make sure that if we are in navigation mode, we
        # never put the cursor after the last character of a line. (Unless it's
        # an empty line.)
        if (
                self._vi_mode == ViMode.NAVIGATION and
                self.line.document.is_cursor_at_the_end_of_line and
                len(self.line.document.current_line) > 0):
            self.line.cursor_position -= 1

    def _needs_to_save(self, current_method):
        # Don't create undo entries in the middle of executing a macro.
        # (We want to be able to undo the macro in its whole.)
        if self._playing_macro:
            return False

        return super(ViInputStreamHandler, self)._needs_to_save(current_method)

    def escape(self):
        """ Escape goes to vi navigation mode. """
        self._vi_mode = ViMode.NAVIGATION
        self._current_handles = self._all_navigation_handles

        # Reset arg count.
        self._arg_count = None

        # Quit incremental search (if enabled.)
        if self.line.mode == LineMode.INCREMENTAL_SEARCH:
            self.line.exit_isearch()

    def enter(self):
        if self.line.mode == LineMode.INCREMENTAL_SEARCH:
            self.line.exit_isearch(restore_original_line=False)

        elif self._vi_mode == ViMode.NAVIGATION:
            self._vi_mode = ViMode.INSERT
            self.line.return_input()

        else:
            super(ViInputStreamHandler, self).enter()

    def backspace(self):
        # In Vi-mode, either move cursor or delete character.
        if self._vi_mode == ViMode.INSERT:
            self.line.delete_before_cursor()
        else:
            self.line.cursor_left()

    def ctrl_v(self):
        # TODO: Insert a character literally (quoted insert).
        pass

    def ctrl_n(self):
        self.line.complete_next()

    def ctrl_p(self):
        self.line.complete_previous()

    def _get_navigation_mode_handles(self):
        """
        Create a dictionary that maps the vi key binding to their handlers.
        """
        handles = {}
        line = self.line

        def handle(key):
            """ Decorator that registeres the handler function in the handles dict. """
            def wrapper(func):
                handles[key] = func
                return func
            return wrapper

        # List of navigation commands: http://hea-www.harvard.edu/~fine/Tech/vi.html

        @handle('a')
        def _(arg):
            self._vi_mode = ViMode.INSERT
            line.cursor_position += line.document.get_cursor_right_position()

        @handle('A')
        def _(arg):
            self._vi_mode = ViMode.INSERT
            self.line.cursor_position += self.line.document.get_end_of_line_position()

        @handle('C') # Same as 'c$' (which is implemented elsewhere.)
        def _(arg):
            # Change to end of line.
            deleted = line.delete(count=self.line.document.get_end_of_line_position())
            if deleted:
                data = ClipboardData(deleted)
                line.set_clipboard(data)
            self._vi_mode = ViMode.INSERT

        @handle('cc')
        @handle('S')
        def _(arg): # TODO: implement 'arg'
            """ Change current line """
            # We copy the whole line.
            data = ClipboardData(line.document.current_line, ClipboardDataType.LINES)
            line.set_clipboard(data)

            # But we delete after the whitespace
            self.line.cursor_position += self.line.document.get_start_of_line_position(after_whitespace=True)
            line.delete(count=self.line.document.get_end_of_line_position())
            self._vi_mode = ViMode.INSERT

        class CursorRegion(object):
            """ Return struct for functions wrapped in ``change_delete_move_yank_handler``. """
            def __init__(self, start, end=0):
                self.start = start
                self.end = end

            def get_sorted(self):
                if self.start < self.end:
                    return self.start, self.end
                else:
                    return self.end, self.start

        def change_delete_move_yank_handler(keys, no_move_handler=False, needs_one_more_character=False):
            """
            Register a change/delete/move/yank handlers. e.g.  'dw'/'cw'/'w'/'yw'
            The decorated function should return a ``CursorRegion``.
            This decorator will create both the 'change', 'delete' and move variants,
            based on that ``CursorRegion``.
            """
            # TODO: Also do '>' and '<' indent/unindent operators.
            def decorator(func):
                def call_function(arg, done_callback):
                    """ Call the original function. If we need an additional
                    character, like for e.g. 'fx', then set a callback, and
                    pass the result later into that function. """
                    if needs_one_more_character:
                        def cb(char):
                            done_callback(func(arg, char))
                        self._one_character_callback = cb
                    else:
                        done_callback(func(arg))

                if not no_move_handler:
                    @handle('%s' % keys)
                    def move(arg):
                        """ Create move handler. """
                        def done(region):
                            line.cursor_position += region.start
                        call_function(arg, done)

                @handle('y%s' % keys)
                def yank_handler(arg):
                    """ Create yank handler. """
                    def done(region):
                        start, end = region.get_sorted()
                        substring = line.text[line.cursor_position + start : line.cursor_position + end]

                        if substring:
                            line.set_clipboard(ClipboardData(substring))
                    call_function(arg, done)

                def create(delete_only):
                    """ Create delete and change handlers. """
                    @handle('%s%s' % ('cd'[delete_only], keys))
                    @handle('%s%s' % ('cd'[delete_only], keys))
                    def _(arg):
                        def done(region):
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
                                self._vi_mode = ViMode.INSERT
                        call_function(arg, done)

                create(True)
                create(False)
                return func
            return decorator

        @change_delete_move_yank_handler('b') # Move one word or token left.
        @change_delete_move_yank_handler('B') # Move one non-blank word left ((# TODO: difference between 'b' and 'B')
        def _(arg):
            return CursorRegion(line.document.find_start_of_previous_word(count=arg) or 0)

        @change_delete_move_yank_handler('$')
        def _(arg):
            """ 'c$', 'd$' and '$':  Delete/change/move until end of line. """
            return CursorRegion(line.document.get_end_of_line_position())

        @change_delete_move_yank_handler('w') # TODO: difference between 'w' and 'W'
        def _(arg):
            """ 'cw', 'de', 'w': Delete/change/move one word.  """
            return CursorRegion(line.document.find_next_word_beginning(count=arg) or 0)

        @change_delete_move_yank_handler('e') # TODO: difference between 'e' and 'E'
        def _(arg):
            """ 'ce', 'de', 'e' """
            end = line.document.find_next_word_ending(count=arg)
            return CursorRegion(end - 1 if end else 0)

        @change_delete_move_yank_handler('iw', no_move_handler=True)
        def _(arg):
            """ ciw and diw """
            # Change inner word: change word under cursor.
            start, end = line.document.find_boundaries_of_current_word()
            return CursorRegion(start, end)

        @change_delete_move_yank_handler('^')
        def _(arg):
            """ 'c^', 'd^' and '^': Soft start of line, after whitespace. """
            return CursorRegion(line.document.get_start_of_line_position(after_whitespace=True))

        @change_delete_move_yank_handler('0')
        def _(arg):
            """ 'c0', 'd0' and '0': Hard start of line, before whitespace. """
            return CursorRegion(line.document.get_start_of_line_position(after_whitespace=False))

        def create_ci_ca_handles(ci_start, ci_end, inner):
                    # TODO: 'dab', 'dib', (brackets or block) 'daB', 'diB', Braces.
                    # TODO: 'dat', 'dit', (tags (like xml)
            """
            Delete/Change string between this start and stop character. But keep these characters.
            This implements all the ci", ci<, ci{, ci(, di", di<, ca", ca<, ... combinations.
            """
            @change_delete_move_yank_handler('ai'[inner] + ci_start, no_move_handler=True)
            @change_delete_move_yank_handler('ai'[inner] + ci_end, no_move_handler=True)
            def _(arg):
                start = line.document.find_backwards(ci_start, in_current_line=True)
                end = line.document.find(ci_end, in_current_line=True)

                if start is not None and end is not None:
                    offset = 0 if inner else 1
                    return CursorRegion(start + 1 - offset, end + offset)

        for inner in (False, True):
            for ci_start  , ci_end in [ ('"', '"'), ("'", "'"), ("`", "`"),
                                ('[', ']'), ('<', '>'), ('{', '}'), ('(', ')') ]:
                create_ci_ca_handles(ci_start, ci_end, inner)

        @change_delete_move_yank_handler('f', needs_one_more_character=True)
        def _(arg, char):
            # Go to next occurance of character. Typing 'fx' will move the
            # cursor to the next occurance of character. 'x'.
            self._last_character_find = (char, False)
            match = line.document.find(char, in_current_line=True, count=arg)
            return CursorRegion(match or 0)

        @change_delete_move_yank_handler('F', needs_one_more_character=True)
        def _(arg, char):
            # Go to previous occurance of character. Typing 'Fx' will move the
            # cursor to the previous occurance of character. 'x'.
            self._last_character_find = (char, True)
            return CursorRegion(line.document.find_backwards(char, in_current_line=True, count=arg) or 0)

        @change_delete_move_yank_handler('t', needs_one_more_character=True)
        def _(arg, char):
            # Move right to the next occurance of c, then one char backward.
            self._last_character_find = (char, False)
            match = line.document.find(char, in_current_line=True, count=arg)
            return CursorRegion(match - 1 if match else 0)

        @change_delete_move_yank_handler('T', needs_one_more_character=True)
        def _(arg, char):
            # Move left to the previous occurance of c, then one char forward.
            self._last_character_find = (char, True)
            match = line.document.find_backwards(char, in_current_line=True, count=arg)
            return CursorRegion(match + 1 if match else 0)

        def repeat(reverse):
            """ Create ',' and ';' commands. """
            @change_delete_move_yank_handler(',' if reverse else ';')
            def _(arg):
                # Repeat the last 'f'/'F'/'t'/'T' command.
                pos = 0

                if self._last_character_find:
                    char, backwards = self._last_character_find

                    if reverse:
                        backwards = not backwards

                    if backwards:
                        pos = line.document.find_backwards(char, in_current_line=True, count=arg)
                    else:
                        pos = line.document.find(char, in_current_line=True, count=arg)
                return CursorRegion(pos or 0)
        repeat(True)
        repeat(False)

        @change_delete_move_yank_handler('h')
        def _(arg):
            """ Implements 'ch', 'dh', 'h': Cursor left. """
            return CursorRegion(line.document.get_cursor_left_position(count=arg))

        @change_delete_move_yank_handler('j')
        def _(arg):
            """ Implements 'cj', 'dj', 'j', ... Cursor up. """
            return CursorRegion(line.document.get_cursor_down_position(count=arg))

        @change_delete_move_yank_handler('k')
        def _(arg):
            """ Implements 'ck', 'dk', 'k', ... Cursor up. """
            return CursorRegion(line.document.get_cursor_up_position(count=arg))

        @change_delete_move_yank_handler('l')
        @change_delete_move_yank_handler(' ')
        def _(arg):
            """ Implements 'cl', 'dl', 'l', 'c ', 'd ', ' '. Cursor right. """
            return CursorRegion(line.document.get_cursor_right_position(count=arg))

        @change_delete_move_yank_handler('H')
        def _(arg):
            """ Implements 'cH', 'dH', 'H'. """
            # Vi moves to the start of the visible region.
            # cursor position 0 is okay for us.
            return CursorRegion(-len(line.document.text_before_cursor))

        @change_delete_move_yank_handler('L')
        def _(arg):
            # Vi moves to the end of the visible region.
            # cursor position 0 is okay for us.
            return CursorRegion(len(line.document.text_after_cursor))

        @change_delete_move_yank_handler('%')
        def _(arg):
            """ Implements 'c%', 'd%', '%, 'y%' """
            # Move to the corresponding opening/closing bracket (()'s, []'s and {}'s).
            return CursorRegion(line.document.matching_bracket_position)

        @change_delete_move_yank_handler('|')
        def _(arg):
            # Move to the n-th column (you may specify the argument n by typing
            # it on number keys, for example, 20|).
            return CursorRegion(line.document.get_column_cursor_position(arg))

        @change_delete_move_yank_handler('gg')
        def _(arg):
            """ Implements 'gg', 'cgg', 'ygg' """
            # Move to the top of the input.
            return CursorRegion(line.document.home_position)

        @handle('D')
        def _(arg):
            deleted = line.delete(count=line.document.get_end_of_line_position())
            line.set_clipboard(ClipboardData(deleted))

        @handle('dd')
        def _(arg):
            """ Delete line. (Or the following 'n' lines. """
            # Split string in before/deleted/after text.
            lines = line.document.lines

            before = '\n'.join(lines[:line.document.cursor_position_row])
            deleted = '\n'.join(lines[line.document.cursor_position_row : line.document.cursor_position_row + arg])
            after = '\n'.join(lines[line.document.cursor_position_row + arg:])

            # Set new text.
            if before and after:
                before = before + '\n'

            line.text = before + after

            # Set cursor position. (At the start of the first 'after' line, after the leading whitespace.)
            line.cursor_position = len(before) + len(after) - len(after.lstrip(' '))

            # Set clipboard data
            line.set_clipboard(ClipboardData(deleted, ClipboardDataType.LINES))

        @handle('G')
        def _(arg):
            # Move to the history line n (you may specify the argument n by
            # typing it on number keys, for example, 15G)
            line.go_to_history(arg - 1)

        @handle('i')
        def _(arg):
            self._vi_mode = ViMode.INSERT

        @handle('I')
        def _(arg):
            self._vi_mode = ViMode.INSERT
            line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

        @handle('J')
        def _(arg):
            for i in range(arg):
                line.join_next_line()

        @handle('n') # XXX: use `change_delete_move_yank_handler`
        def _(arg):
            # TODO:
            pass

            # if line.isearch_state:
            #     # Repeat search in the same direction as previous.
            #     line.search_next(line.isearch_state.isearch_direction)

        @handle('N') # TODO: use `change_delete_move_yank_handler`
        def _(arg):
            # TODO:
            pass

            #if line.isearch_state:
            #    # Repeat search in the opposite direction as previous.
            #    if line.isearch_state.isearch_direction == IncrementalSearchDirection.FORWARD:
            #        line.search_next(IncrementalSearchDirection.BACKWARD)
            #    else:
            #        line.search_next(IncrementalSearchDirection.FORWARD)

        @handle('p')
        def _(arg):
            # Paste after
            for i in range(arg):
                line.paste_from_clipboard()

        @handle('P')
        def _(arg):
            # Paste before
            for i in range(arg):
                line.paste_from_clipboard(before=True)

        @handle('r')
        def _(arg):
            # Replace single character under cursor
            def cb(char):
                line.insert_text(char * arg, overwrite=True)
            self._one_character_callback = cb

        @handle('R')
        def _(arg):
            # Go to 'replace'-mode.
            self._vi_mode = ViMode.REPLACE

        @handle('s')
        def _(arg):
            # Substitute with new text
            # (Delete character(s) and go to insert mode.)
            data = ClipboardData(''.join(line.delete() for i in range(arg)))
            line.set_clipboard(data)
            self._vi_mode = ViMode.INSERT

        @handle('u')
        def _(arg):
            for i in range(arg):
                line.undo()

        @handle('v')
        def _(arg):
            line.open_in_editor()

        @handle('x')
        def _(arg):
            # Delete character.
            data = ClipboardData(line.delete(count=arg))
            line.set_clipboard(data)

        @handle('X')
        def _(arg):
            data = line.delete_before_cursor()
            line.set_clipboard(data)

        @handle('yy')
        def _(arg):
            # Yank the whole line.
            text = '\n'.join(line.document.lines_from_current[:arg])

            data = ClipboardData(text, ClipboardDataType.LINES)
            line.set_clipboard(data)

        @handle('+')
        def _(arg):
            # Move to first non whitespace of next line
            line.cursor_position += line.document.get_cursor_down_position(count=arg)
            line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

        @handle('-')
        def _(arg):
            # Move to first non whitespace of previous line
            line.cursor_position += line.document.get_cursor_up_position(count=arg)
            line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

        @handle('{')
        def _(arg):
            # Move to previous blank-line separated section.
            for i in range(arg):
                index = line.document.find_previous_matching_line(
                                lambda text: not text or text.isspace())

                if index is not None:
                    line.cursor_position += line.document.get_cursor_up_position(count=index)

        @handle('}')
        def _(arg):
            # Move to next blank-line separated section.
            for i in range(arg):
                index = line.document.find_next_matching_line(
                                lambda text: not text or text.isspace())

                if index is not None:
                    line.cursor_position += line.document.get_cursor_down_position(count=index)

        @handle('>>')
        def _(arg):
            # Indent lines.
            current_line = line.document.cursor_position_row
            line_range = range(current_line, current_line + arg)
            line.transform_lines(line_range, lambda l: '    ' + l)

            line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

        @handle('<<')
        def _(arg):
            # Unindent current line.
            current_line = line.document.cursor_position_row
            line_range = range(current_line, current_line + arg)

            def transform(text):
                if text.startswith('    '):
                    return text[4:]
                else:
                    return text.lstrip()

            line.transform_lines(line_range, transform)
            line.cursor_position += line.document.get_start_of_line_position(after_whitespace=True)

        @handle('O')
        def _(arg):
            # Open line above and enter insertion mode
            line.insert_line_above()
            self._vi_mode = ViMode.INSERT

        @handle('o')
        def _(arg):
            # Open line below and enter insertion mode
            line.insert_line_below()
            self._vi_mode = ViMode.INSERT

        @handle('q')
        def _(arg):
            # Start/stop recording macro.
            if self._macro_recording_register:
                # Save macro.
                self._macros[self._macro_recording_register] = self._macro_recording_calls
                self._macro_recording_register = None
            else:
                # Start new macro.
                def cb(char):
                    self._macro_recording_register = char
                    self._macro_recording_calls = []

                self._one_character_callback = cb

        @handle('@')
        def _(arg):
            # Execute macro.
            def cb(char):
                if char in self._macros:
                    self._playing_macro = True

                    for command in self._macros[char]:
                        self(*command)

                    self._playing_macro = False

            self._one_character_callback = cb

        @handle('~')
        def _(arg):
            """ Reverse case of current character and move cursor forward. """
            c = line.document.current_char
            if c is not None and c != '\n':
                c = (c.upper() if c.islower() else c.lower())
                line.insert_text(c, overwrite=True)

        @handle('/')
        def _(arg):
            # Search history backward for a command matching string.
            self.line.reverse_search()
            self._vi_mode = ViMode.INSERT # We have to be able to insert the search string.

        @handle('?')
        def _(arg):
            # Search history forward for a command matching string.
            self.line.forward_search()
            self._vi_mode = ViMode.INSERT # We have to be able to insert the search string.

        @handle('#')
        def _(arg):
            # Go to previous occurence of this word.
            pass

        @handle('*')
        def _(arg):
            # Go to next occurence of this word.
            pass

        @handle('(')
        def _(arg):
            # TODO: go to begin of sentence.
            pass

        @handle(')')
        def _(arg):
            # TODO: go to end of sentence.
            pass

        return handles

    def insert_char(self, data):
        """ Insert data at cursor position.  """
        assert len(data) == 1

        if self._one_character_callback:
            self._one_character_callback(data)
            self._one_character_callback = False

        elif self.line.mode == LineMode.INCREMENTAL_SEARCH:
            self.line.insert_text(data)

        elif self._vi_mode == ViMode.NAVIGATION:
            # Always handle numberics to build the arg
            if data in '123456789' or (self._arg_count and data == '0'):
                self.set_arg_count(_arg_count_append(self._arg_count, data))

            # If we have a handle for the current keypress. Call it.
            elif data in self._current_handles:
                # Pass argument to handle.
                arg_count = self.get_arg_count()

                # Safe state (except if we called the 'undo' action.)
                if data != 'u':
                    self.line.save_to_undo_stack()

                # Call handler
                self._current_handles[data](arg_count or 1)
                self._current_handles = self._all_navigation_handles

            # If there are several combitations of handles, starting with the
            # keys that were already pressed. Reduce to this subset of
            # handlers.
            elif data in [ k[0] for k in self._current_handles.keys() ]:
                self._current_handles = { k[1:]:h for k, h in self._current_handles.items() if k[0] == data }

            # No match. Reset.
            else:
                self._current_handles = self._all_navigation_handles

        # In replace/text mode.
        elif self._vi_mode == ViMode.REPLACE:
            self.line.insert_text(data, overwrite=True)

        # In insert/text mode.
        elif self._vi_mode == ViMode.INSERT:
            super(ViInputStreamHandler, self).insert_char(data)


def _arg_count_append(current, data):
    """
    Utility for manupulating the arg-count string.

    :param current: int or None
    :param data: the typed digit as string
    :returns: int or None
    """
    assert data in '-0123456789'

    if current is None:
        if data == '-':
            data = '-1'
        result = int(data)
    else:
        result = int("%s%s" % (current, data))

    # Don't exceed a million.
    if int(result) >= 1000000:
        result = None

    return result
