"""

::

    from prompt_toolkit.contrib.python_import import PythonCommandLine

    cli = PythonCommandLine()
    cli.read_input()
"""
from __future__ import unicode_literals

from pygments.lexers import PythonLexer
from pygments.style import Style
from pygments.token import Keyword, Operator, Number, Name, Error, Comment, Token

from prompt_toolkit import CommandLine
from prompt_toolkit.code import Completion, Code, ValidationError
from prompt_toolkit.enums import LineMode
from prompt_toolkit.history import FileHistory, History
from prompt_toolkit.inputstream_handler import ViInputStreamHandler, EmacsInputStreamHandler, ViMode
from prompt_toolkit.line import Line
from prompt_toolkit.prompt import Prompt

import jedi
import re


__all__ = ('PythonCommandLine', )


class PythonStyle(Style):
    background_color = None
    styles = {
        Keyword:                       '#ee00ee',
        Operator:                      '#aa6666',
        Number:                        '#ff0000',
        Name:                          '#008800',
        Token.Literal.String:          '#440000',

        Error:                         '#000000 bg:#ff8888',
        Comment:                       '#0000dd',
        Token.Bash:                    '#333333',
        Token.IPython:                 '#660066',

        # Signature highlighting.
        Token.Signature:               '#888888',
        Token.Signature.Operator:      'bold #888888',
        Token.Signature.CurrentName:   'bold underline #888888',

        # Highlighting for the reverse-search prompt.
        Token.Prompt:                  'bold #004400',
        Token.Prompt.ISearch.Bracket:  'bold #440000',
        Token.Prompt.ISearch:          '#550000',
        Token.Prompt.ISearch.Backtick: 'bold #550033',
        Token.Prompt.ISearch.Text:     'bold',
        Token.Prompt.SecondLinePrefix: 'bold #888888',
        Token.Prompt.ArgText:          'bold',

        Token.Toolbar:                 'bg:#222222 #aaaaaa',
        Token.Toolbar.Off:             'bg:#222222 #888888',
        Token.Toolbar.On:              'bg:#222222 #ffffff',
        Token.Toolbar.Mode:            'bg:#222222 #ffffaa',

        # Completion menu
        Token.CompletionMenu.CurrentCompletion: 'bg:#dddddd #000000',
        Token.CompletionMenu.Completion:        'bg:#888888 #ffff88',
        Token.CompletionMenu.ProgressButton:    'bg:#000000',
        Token.CompletionMenu.ProgressBar:       'bg:#aaaaaa',

        # Grayed
        Token.Aborted:                 '#aaaaaa',

        Token.ValidationError:         'bg:#aa0000 #ffffff',
    }


class _PythonInputStreamHandlerMixin(object):
    """
    Extensions to the input stream handler for custom 'enter' behaviour.
    """
    def F6(self):
        """ Enable/Disable paste mode. """
        self._line.paste_mode = not self._line.paste_mode
        if self._line.paste_mode:
            self._line.is_multiline = True

    def F7(self):
        self._line.is_multiline = not self._line.is_multiline

    def _auto_enable_multiline(self):
        """
        (Temporarily) enable multiline when pressing enter.
        When:
        - We press [enter] after a color or backslash (line continuation).
        - After unclosed brackets.
        """
        def is_empty_or_space(s):
            return s == '' or s.isspace()
        cursor_at_the_end = self._line.document.cursor_at_the_end

        # If we just typed a colon, or still have open brackets, always insert a real newline.
        if cursor_at_the_end and (self._line._colon_before_cursor() or
                                  self._line._has_unclosed_brackets()):
            self._line.is_multiline = True

        # If the character before the cursor is a backslash (line continuation
        # char), insert a new line.
        elif cursor_at_the_end and (self._line.document.text_before_cursor[-1:] == '\\'):
            self._line.is_multiline = True

    def tab(self):
        # When the 'tab' key is pressed with only whitespace character before the
        # cursor, do autocompletion. Otherwise, insert indentation.
        current_char = self._line.document.current_line_before_cursor
        if not current_char or current_char.isspace():
            self._line.insert_text('    ')
        else:
            self._line.complete_next()

    def backtab(self):
        if self._line.mode == LineMode.COMPLETE:
            self._line.complete_previous()

    def enter(self):
        self._auto_enable_multiline()
        super(_PythonInputStreamHandlerMixin, self).enter()


class PythonViInputStreamHandler(_PythonInputStreamHandlerMixin, ViInputStreamHandler):
    pass


class PythonEmacsInputStreamHandler(_PythonInputStreamHandlerMixin, EmacsInputStreamHandler):
    pass


class PythonLine(Line):
    """
    Custom `Line` class with some helper functions.
    """
    def reset(self, *a, **kw):
        super(PythonLine, self).reset(*a, **kw)

        #: Boolean `paste` flag. If True, don't insert whitespace after a
        #: newline.
        self.paste_mode = False

        #: Boolean `multiline` flag. If True, [Enter] will always insert a
        #: newline, and it is required to use [Meta+Enter] execute commands.
        self.is_multiline = False

        # Code signatures. (This is set asynchronously after a timeout.)
        self.signatures = []

    def _text_changed(self):
        self.is_multiline = '\n' in self.text

    def _colon_before_cursor(self):
        return self.document.text_before_cursor[-1:] == ':'

    def _has_unclosed_brackets(self):
        """ Starting at the end of the string. If we find an opening bracket
        for which we didn't had a closing one yet, return True. """
        text = self.document.text_before_cursor
        stack = []

        # Ignore braces inside strings
        text = re.sub(r'''('[^']*'|"[^"]*")''', '', text) # XXX: handle escaped quotes.!

        for c in reversed(text):
            if c in '])}':
                stack.append(c)

            elif c in '[({':
                if stack:
                    if ((c == '[' and stack[-1] == ']') or
                        (c == '{' and stack[-1] == '}') or
                        (c == '(' and stack[-1] == ')')):
                        stack.pop()
                else:
                    # Opening bracket for which we didn't had a closing one.
                    return True

        return False

    def newline(self):
        r"""
        Insert \n at the cursor position. Also add necessary padding.
        """
        insert_text = super(PythonLine, self).insert_text

        if self.paste_mode or self.document.current_line_after_cursor:
            insert_text('\n')
        else:
            # Go to new line, but also add indentation.
            current_line = self.document.current_line_before_cursor.rstrip()
            insert_text('\n')

            # Copy whitespace from current line
            for c in current_line:
                if c.isspace():
                    insert_text(c)
                else:
                    break

            # If the last line ends with a colon, add four extra spaces.
            if current_line[-1:] == ':':
                for x in range(4):
                    insert_text(' ')

    def cursor_left(self):
        """
        When moving the cursor left in the left indentation margin, move four
        spaces at a time.
        """
        before_cursor = self.document.current_line_before_cursor

        if not self.paste_mode and not self.mode == LineMode.INCREMENTAL_SEARCH and before_cursor.isspace():
            count = 1 + (len(before_cursor) - 1) % 4
        else:
            count = 1

        for i in range(count):
            super(PythonLine, self).cursor_left()

    def cursor_right(self):
        """
        When moving the cursor right in the left indentation margin, move four
        spaces at a time.
        """
        before_cursor = self.document.current_line_before_cursor
        after_cursor = self.document.current_line_after_cursor

        # Count space characters, after the cursor.
        after_cursor_space_count = len(after_cursor) - len(after_cursor.lstrip())

        if (not self.paste_mode and not self.mode == LineMode.INCREMENTAL_SEARCH and
                    (not before_cursor or before_cursor.isspace()) and after_cursor_space_count):
            count = min(4, after_cursor_space_count)
        else:
            count = 1

        for i in range(count):
            super(PythonLine, self).cursor_right()


class PythonPrompt(Prompt):
    def __init__(self, line, code, pythonline):
        super(PythonPrompt, self).__init__(line, code)
        self._pythonline = pythonline

    @property
    def _prefix(self):
        return (Token.Prompt, 'In [%s]' % self._pythonline.current_statement_index)

    def get_default_prompt(self):
        yield self._prefix
        yield (Token.Prompt, ': ')

    def get_isearch_prompt(self):
        yield self._prefix
        yield (Token.Prompt, ': ')

    def get_arg_prompt(self):
        yield self._prefix
        yield (Token.Prompt, ': ')

    def get_help_tokens(self):
        """
        When inside functions, show signature.
        """
        result = []
        result.append((Token, '\n'))

        if self.line.mode == LineMode.INCREMENTAL_SEARCH:
            result.extend(list(super(PythonPrompt, self).get_isearch_prompt()))
        elif self.line._arg_prompt_text:
            result.extend(list(super(PythonPrompt, self).get_arg_prompt()))
        elif self.line.validation_error:
            result.extend(self._get_error_tokens())
        else:
            result.extend(self._get_signature_tokens())

        result.extend(self._get_toolbar_tokens())
        return result

    def _get_signature_tokens(self):
        result = []
        append = result.append
        Signature = Token.Signature

        if self.line.signatures:
            sig = self.line.signatures[0] # Always take the first one.

            append((Token, '           '))
            append((Signature, sig.full_name))
            append((Signature.Operator, '('))

            for i, p in enumerate(sig.params):
                if i == sig.index:
                    append((Signature.CurrentName, str(p.name)))
                else:
                    append((Signature, str(p.name)))
                append((Signature.Operator, ', '))

            result.pop() # Pop last comma
            append((Signature.Operator, ')'))

        return result

    def _get_error_tokens(self):
        if self.line.validation_error:
            text = '%s (line=%s column=%s)' % (
                    self.line.validation_error.message,
                    self.line.validation_error.line + 1,
                    self.line.validation_error.column + 1)
            return [(Token.ValidationError, text)]
        else:
            return []

    def _get_toolbar_tokens(self):
        result = []
        append = result.append
        TB = Token.Toolbar

        append((Token, '\n  '))
        append((TB, '  '))

        # Mode
        if self.line.mode == LineMode.INCREMENTAL_SEARCH:
            append((TB.Mode, '(SEARCH)'))
            append((TB, '  '))
        elif self._pythonline.vi_mode:
            mode = self._pythonline._inputstream_handler._vi_mode
            if mode == ViMode.NAVIGATION:
                append((TB.Mode, '(NAV)'))
                append((TB, '     '))
            elif mode == ViMode.INSERT:
                append((TB.Mode, '(INSERT)'))
                append((TB, '  '))
            elif mode == ViMode.REPLACE:
                append((TB.Mode, '(REPLACE)'))
                append((TB, ' '))

            if self._pythonline._inputstream_handler.is_recording_macro:
                append((TB.Mode, 'recording'))
                append((TB, ' '))

        else:
            append((TB.Mode, '(emacs)'))
            append((TB, ' '))

        # Position in history.
        result.append((TB, '%i/%i ' % (self.line._working_index + 1, len(self.line._working_lines))))

        # Shortcuts.
        if self.line.mode == LineMode.INCREMENTAL_SEARCH:
            append((TB, '[Ctrl-G] Cancel search'))
        else:
            if self.line.paste_mode:
                append((TB.On, '[F6] Paste mode (on)  '))
            else:
                append((TB.Off, '[F6] Paste mode (off) '))

            if self.line.is_multiline:
                append((TB.On, '[F7] Multiline (on)  '))
            else:
                append((TB.Off, '[F7] Multiline (off) '))

            if self.line.is_multiline:
                append((TB, '[Meta+Enter] Execute'))
            else:
                append((TB, '                    '))

        append((TB, '  '))

        return result


class PythonCode(Code):
    lexer = PythonLexer

    def __init__(self, document, globals, locals):
        self._globals = globals
        self._locals = locals
        super(PythonCode, self).__init__(document)

    def validate(self):
        """ Check input for Python syntax errors. """
        try:
            compile(self.text, '<input>', 'exec')
        except SyntaxError as e:
            raise ValidationError(e.lineno - 1, e.offset - 1, 'Syntax Error')

    def _get_tokens(self):
        """ Overwrite parent function, to change token types of non-matching
        brackets to Token.Error for highlighting. """
        result = super(PythonCode, self)._get_tokens()

        stack = [] # Pointers to the result array

        for index, (token, text) in enumerate(result):
            top = result[stack[-1]][1] if stack else ''

            if text in '({[]})':
                if text in '({[':
                    # Put open bracket on the stack
                    stack.append(index)

                elif (text == ')' and top == '(' or
                      text == '}' and top == '{' or
                      text == ']' and top == '['):
                    # Match found
                    stack.pop()
                else:
                    # No match for closing bracket.
                    result[index] = (Token.Error, text)

        # Highlight unclosed tags that are still on the stack.
        for index in stack:
            result[index] = (Token.Error, result[index][1])

        return result

    def _get_jedi_script(self):
        try:
            return jedi.Interpreter(self.text,
                    column=self.document.cursor_position_col,
                    line=self.document.cursor_position_row + 1,
                    path='input-text',
                    namespaces=[ self._locals, self._globals ])

        except jedi.common.MultiLevelStopIteration:
            # This happens when the document is just a backslash.
            return None
        except ValueError:
            # Invalid cursor position.
            # ValueError('`column` parameter is not in a valid range.')
            return None

    def get_completions(self):
        """ Ask jedi to complete. """
        script = self._get_jedi_script()

        if script:
            for c in script.completions():
                yield Completion(c.name, c.complete)


class PythonCommandLine(CommandLine):
    line_factory = PythonLine

    enable_concurency = True

    def history_factory(self):
        if self.history_filename:
            return FileHistory(self.history_filename)
        else:
            return History()

    @property
    def inputstream_handler_factory(self):
        if self.vi_mode:
            return PythonViInputStreamHandler
        else:
            return PythonEmacsInputStreamHandler

    def prompt_factory(self, line, code):
        # The `PythonPrompt` class needs a reference back in order to show the
        # input method.
        return PythonPrompt(line, code, self)

    def code_factory(self, document):
        # The `PythonCode` needs a reference back to this class in order to do
        # autocompletion on the globals/locals.
        return PythonCode(document, self.globals, self.locals)

    def __init__(self, globals=None, locals=None, vi_mode=False, stdin=None, stdout=None, history_filename=None, style=PythonStyle):
        self.globals = globals or {}
        self.globals.update({ k: getattr(__builtins__, k) for k in dir(__builtins__) })
        self.locals = locals or {}
        self.history_filename = history_filename
        self.style = style

        self.vi_mode = vi_mode
        self.get_signatures_thread_running = False

        #: Incremeting integer counting the current statement.
        self.current_statement_index = 1

        super(PythonCommandLine, self).__init__(stdin=stdin, stdout=stdout)

    def on_input_timeout(self, code_obj):
        """
        When there is no input activity,
        in another thread, get the signature of the current code.
        """
        # Never run multiple get-signature threads.
        if self.get_signatures_thread_running:
            return
        self.get_signatures_thread_running = True

        def run():
            script = code_obj._get_jedi_script()

            # Show signatures in help text.
            if script:
                try:
                    signatures = script.call_signatures()
                except ValueError:
                    # e.g. in case of an invalid \x escape.
                    signatures = []
            else:
                signatures = []

            self.get_signatures_thread_running = False

            # Set signatures and redraw if the text didn't change in the
            # meantime. Otherwise request new signatures.
            if self._line.text == code_obj.text:
                self._line.signatures = signatures
                self.request_redraw()
            else:
                self.on_input_timeout(self._line.create_code_obj())

        self.run_in_executor(run)
