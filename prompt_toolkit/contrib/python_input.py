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
from prompt_toolkit.prompt import Prompt, TokenList, BracketsMismatchProcessor, PopupCompletionMenu, HorizontalCompletionMenu

import jedi
import re
import sys


__all__ = (
    'PythonCommandLine',
    'AutoCompletionStyle',
)


class AutoCompletionStyle:
    #: tab/double-tab completion
    # TRADITIONAL = 'traditional' # TODO: not implemented yet.

    #: Pop-up
    POPUP_MENU = 'popup-menu'

    #: Horizontal list
    HORIZONTAL_MENU = 'horizontal-menu'

    #:Pop-up menu that also displays the references to the Python modules.
    EXTENDED_POPUP_MENU = 'extended-popup-menu'

    #: No visualisation
    NONE = 'none'


class PythonStyle(Style):
    background_color = None
    styles = {
        Keyword:                       '#ee00ee',
        Operator:                      '#ff6666 bold',
        Number:                        '#ff0000',
        Name:                          '#008800',
        Name.Namespace:                '#008800 underline',
        Name.Decorator:                '#aa22ff',

        Token.Literal.String:          '#ba4444 bold',

        Error:                         '#000000 bg:#ff8888',
        Comment:                       '#0000dd',
        Token.Bash:                    '#333333',
        Token.IPython:                 '#660066',

        Token.IncrementalSearchMatch:         '#ffffff bg:#4444aa',
        Token.IncrementalSearchMatch.Current: '#ffffff bg:#44aa44',

        # Signature highlighting.
        Token.Signature:               '#888888',
        Token.Signature.Operator:      'bold #888888',
        Token.Signature.CurrentName:   'bold underline #888888',

        # Highlighting for the reverse-search prompt.
        Token.Prompt:                     'bold #008800',
        Token.Prompt.ISearch:             'noinherit',
        Token.Prompt.ISearch.Text:        'bold',
        Token.Prompt.ISearch.Text.NoMatch: 'bg:#aa4444 #ffffff',

        Token.Prompt.SecondLinePrefix: 'bold #888888',
        Token.Prompt.LineNumber:       '#bbbbbb',# #ffffff',
        Token.Prompt.Arg:              'noinherit',
        Token.Prompt.Arg.Text:          'bold',

        Token.Toolbar:                 'bg:#222222 #aaaaaa',
        Token.Toolbar.Off:             'bg:#222222 #888888',
        Token.Toolbar.On:              'bg:#222222 #ffffff',
        Token.Toolbar.Mode:            'bg:#222222 #ffffaa',
        Token.Toolbar.PythonVersion:   'bg:#222222 #ffffff bold',

        # Completion menu
        Token.CompletionMenu.CurrentCompletion:      'bg:#dddddd #000000',
        Token.CompletionMenu.Completion:             'bg:#888888 #ffffbb',
        Token.CompletionMenu.ProgressButton:         'bg:#000000',
        Token.CompletionMenu.ProgressBar:            'bg:#aaaaaa',
        Token.CompletionMenu.JediDescription:        'bg:#888888 #cccccc',
        Token.CompletionMenu.CurrentJediDescription: 'bg:#bbbbbb #000000',

        Token.WildMenu.Completion:              'bg:#dddddd #000000',
        Token.WildMenu.CurrentCompletion:       'bg:#888888 #ffffbb',
        Token.WildMenu:                         'bg:#dddddd',
        Token.WildMenu.Arrow:                   'bg:#dddddd #888888',

        # Grayed
        Token.Aborted:                 '#aaaaaa',

        Token.ValidationError:         'bg:#aa0000 #ffffff',
    }


class _PythonInputStreamHandlerMixin(object): # XXX: Don't use Mixins for this. There are better solutions.
    """
    Extensions to the input stream handler for custom 'enter' behaviour.
    """
    def F6(self):
        """
        Enable/Disable paste mode.
        """
        self._line.paste_mode = not self._line.paste_mode
        if self._line.paste_mode:
            self._line.is_multiline = True

    def F7(self):
        """
        Enable/Disable multiline mode.
        """
        self._line.is_multiline = not self._line.is_multiline

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
                                  self._line._has_unclosed_brackets() or
                                  self._line._starting_with_at()):
            self._line.is_multiline = True

        # If the character before the cursor is a backslash (line continuation
        # char), insert a new line.
        elif cursor_at_the_end and (self._line.document.text_before_cursor[-1:] == '\\'):
            self._line.is_multiline = True


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

    def _starting_with_at(self):
        """ True when the line starts with a decorator. """
        return self.text.startswith('@')

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
    input_processors = [ BracketsMismatchProcessor() ]

    def __init__(self, render_context, pythonline):
        super(PythonPrompt, self).__init__(render_context)
        self._pythonline = pythonline

    @property
    def tokens_before_input(self):
        return [(Token.Prompt, 'In [%s]: ' % self._pythonline.current_statement_index)]

    @property
    def completion_menu(self):
        style = self._pythonline.autocompletion_style

        if style == AutoCompletionStyle.POPUP_MENU:
            return PopupCompletionMenu()
        elif style == AutoCompletionStyle.HORIZONTAL_MENU:
            return HorizontalCompletionMenu()
        elif style == AutoCompletionStyle.EXTENDED_POPUP_MENU:
            return ExtendedPopupCompletionMenu()

    def get_help_tokens(self):
        """
        When inside functions, show signature.
        """
        result = []
        result.append((Token, '\n'))

        if self.line.mode == LineMode.INCREMENTAL_SEARCH:
            result.extend(self.isearch_prompt)
        elif self.line._arg_prompt_text:
            result.extend(self.arg_prompt)
        elif self.line.validation_error:
            result.extend(self._get_error_tokens())
        else:
            result.extend(self._get_signature_tokens())

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

        append((Signature, ' \n'))
                            # Note the space before the newline.
                            # This is to make sure that this line gets at least
                            # some content in the screen, so that we don't put
                            # the toolbar here already.
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

    def create_left_input_margin(self, screen, row):
        prompt_width = len(TokenList(self.tokens_before_input))

        text = '%i. ' % (row + 1)
        text = ' ' * (prompt_width - len(text)) + text

        screen.write_highlighted([
            (Token.Prompt.LineNumber, text)
        ])

    def write_after_input(self, screen):
        screen.write_highlighted(list(self.get_help_tokens()))

    def write_to_screen(self, screen, last_screen_height):
        super(PythonPrompt, self).write_to_screen(screen, last_screen_height)
        self.write_toolbar(screen, last_screen_height)

    def write_toolbar(self, screen, last_screen_height):
        if not (self.render_context.accept or self.render_context.abort):
            # Draw the menu at the bottom position.
            screen._y = max(screen.current_height, last_screen_height - 1)

            result = TokenList()
            append = result.append
            TB = Token.Toolbar

            append((TB, ' '))

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
            append((TB, '%i/%i ' % (self.line._working_index + 1, len(self.line._working_lines))))

            # Shortcuts.
            if self.line.mode == LineMode.INCREMENTAL_SEARCH:
                append((TB, '[Ctrl-G] Cancel search'))
            else:
                if self.line.paste_mode:
                    append((TB.On, '[F6] Paste mode (on)  '))
                else:
                    append((TB.Off, '[F6] Paste mode (off) '))

                if self.line.is_multiline:
                    append((TB.On, '[F7] Multiline (on)'))
                else:
                    append((TB.Off, '[F7] Multiline (off)'))

                if self.line.is_multiline:
                    append((TB, ' [Meta+Enter] Execute'))

                # Python version
                version = sys.version_info
                append((TB, ' - '))
                append((TB.PythonVersion, 'Python %i.%i.%i' % (version.major, version.minor, version.micro)))

            # Adjust toolbar width.
            if len(result) > screen.columns:
                # Trim toolbar
                result = result[:screen.columns - 3]
                result.append((TB, ' > '))
            else:
                # Extend toolbar until the page width.
                result.append((TB, ' ' * (screen.columns - len(result))))

            screen.write_highlighted([(Token, '\n')])
            screen.write_highlighted(result)


class ExtendedPopupCompletionMenu(PopupCompletionMenu):
    """
    Extended completion menu, which shows more info from Jedi inside the completion menu.
    """
    def get_menu_width(self, complete_state):
        return [
                super(ExtendedPopupCompletionMenu, self).get_menu_width(complete_state),
                max(len(c.jedi_completion.type) for c in complete_state.current_completions)
                ]

    def get_menu_item_tokens(self, completion, is_current_completion, menu_width):
        if is_current_completion:
            token = Token.CompletionMenu.CurrentJediDescription
        else:
            token = Token.CompletionMenu.JediDescription

        return super(ExtendedPopupCompletionMenu, self).get_menu_item_tokens(completion, is_current_completion, menu_width[0]) + [
                (token, ' %%-%is ' % menu_width[1] % completion.jedi_completion.type or 'none') ]


class PythonCompletion(Completion):
    def __init__(self, display, suffix, jedi_completion): # XXX: rename suffix to 'addition'
        super(PythonCompletion, self).__init__(display, suffix)
        self.jedi_completion = jedi_completion


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
            # Note, the 'or 1' for offset is required because Python 2.7
            # gives `None` as offset in case of '4=4' as input. (Looks like
            # fixed in Python 3.)
            raise ValidationError(e.lineno - 1, (e.offset or 1) - 1, 'Syntax Error')

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
                #yield Completion('%s %s|%s' % (c.name, c.module_name, c.full_name), c.complete)
                yield PythonCompletion(c.name, c.complete, c)


class PythonCommandLine(CommandLine):
    line_factory = PythonLine

    enable_concurency = True

    def __init__(self, globals=None, locals=None, vi_mode=False, stdin=None, stdout=None, history_filename=None,
                    style=PythonStyle, autocompletion_style=AutoCompletionStyle.POPUP_MENU):

        self.globals = globals or {}
        self.globals.update({k: getattr(__builtins__, k) for k in dir(__builtins__)})
        self.locals = locals or {}
        self.history_filename = history_filename
        self.style = style
        self.autocompletion_style = autocompletion_style

        self.vi_mode = vi_mode
        self.get_signatures_thread_running = False

        #: Incremeting integer counting the current statement.
        self.current_statement_index = 1

        super(PythonCommandLine, self).__init__(stdin=stdin, stdout=stdout)

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

    def prompt_factory(self, render_context):
        # The `PythonPrompt` class needs a reference back in order to show the
        # input method.
        return PythonPrompt(render_context, self)

    def code_factory(self, document):
        # The `PythonCode` needs a reference back to this class in order to do
        # autocompletion on the globals/locals.
        return PythonCode(document, self.globals, self.locals)

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
                except Exception:
                    # Sometimes we still get an exception (TypeError), because
                    # of probably bugs in jedi. We can silence them.
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
