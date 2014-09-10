"""

::

    from prompt_toolkit.contrib.python_import import PythonCommandLineInterface

    cli = PythonCommandLineInterface()
    cli.read_input()
"""
from __future__ import unicode_literals

from pygments.lexers import PythonLexer
from pygments.style import Style
from pygments.token import Keyword, Operator, Number, Name, Error, Comment, Token

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.code import Completion, Code, ValidationError
from prompt_toolkit.enums import InputMode
from prompt_toolkit.history import FileHistory, History
from prompt_toolkit.key_bindings.vi import vi_bindings
from prompt_toolkit.key_bindings.emacs import emacs_bindings
from prompt_toolkit.line import Line
from prompt_toolkit.prompt import Prompt, TokenList, BracketsMismatchProcessor, PopupCompletionMenu, HorizontalCompletionMenu
from prompt_toolkit.keys import Key

import jedi
import platform
import re
import sys


__all__ = (
    'PythonCommandLineInterface',
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
        Token.Prompt.LineNumber:       '#aa6666',
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

        Token.HorizontalMenu.Completion:              '#888888 noinherit',
        Token.HorizontalMenu.CurrentCompletion:       'bold',
        Token.HorizontalMenu:                         'noinherit',
        Token.HorizontalMenu.Arrow:                   'bold #888888',

        # Grayed
        Token.Aborted:                 '#888888',

        Token.ValidationError:         'bg:#aa0000 #ffffff',

        # Vi tildes
        Token.Leftmargin.Tilde:   '#888888',
    }

def _has_unclosed_brackets(text):
    """
    Starting at the end of the string. If we find an opening bracket
    for which we didn't had a closing one yet, return True.
    """
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


def python_bindings(registry, cli_ref):
    """
    Custom key bindings.
    """
    line = cli_ref().line
    handle = registry.add_binding

    @handle(Key.F6)
    def _(event):
        """
        Enable/Disable paste mode.
        """
        line.paste_mode = not line.paste_mode
        if line.paste_mode:
            line.is_multiline = True

    @handle(Key.F7)
    def _(event):
        """
        Enable/Disable multiline mode.
        """
        line.is_multiline = not line.is_multiline

    @handle(Key.Tab)
    def _(event):
        # When the 'tab' key is pressed with only whitespace character before the
        # cursor, do autocompletion. Otherwise, insert indentation.
        current_char = line.document.current_line_before_cursor
        if not current_char or current_char.isspace():
            line.insert_text('    ')
        else:
            line.complete_next()
            event.input_processor.input_mode = InputMode.COMPLETE

    @handle(Key.BackTab, in_mode=InputMode.COMPLETE)
    def _(event):
        line.complete_previous()

    @handle(Key.ControlJ)
    @handle(Key.ControlM)
    def _(event):
        _auto_enable_multiline()

        if line.is_multiline:
            line.newline()
        else:
            line.return_input()

    def _auto_enable_multiline():
        """
        (Temporarily) enable multiline when pressing enter.
        When:
        - We press [enter] after a color or backslash (line continuation).
        - After unclosed brackets.
        """
        def is_empty_or_space(s):
            return s == '' or s.isspace()
        cursor_at_the_end = line.document.is_cursor_at_the_end

        # If we just typed a colon, or still have open brackets, always insert a real newline.
        if cursor_at_the_end and (line.document.text_before_cursor.rstrip()[-1:] == ':' or
                                  _has_unclosed_brackets(line.document.text_before_cursor) or
                                  line.text.startswith('@')):
            line.is_multiline = True

        # If the character before the cursor is a backslash (line continuation
        # char), insert a new line.
        elif cursor_at_the_end and (line.document.text_before_cursor[-1:] == '\\'):
            line.is_multiline = True


class PythonLine(Line):
    """
    Custom `Line` class with some helper functions.
    """
    tempfile_suffix = '.py'

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

    def text_changed(self):
        self.is_multiline = '\n' in self.text

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


class PythonPrompt(Prompt):
    input_processors = [ BracketsMismatchProcessor() ]

    min_height = 7

    @property
    def tokens_before_input(self):
        return [(Token.Prompt, 'In [%s]: ' % self.commandline.current_statement_index)]

    @property
    def completion_menu(self):
        style = self.commandline.autocompletion_style

        if style == AutoCompletionStyle.POPUP_MENU:
            return PopupCompletionMenu()
        elif style == AutoCompletionStyle.HORIZONTAL_MENU:
            return None
        elif style == AutoCompletionStyle.EXTENDED_POPUP_MENU:
            return ExtendedPopupCompletionMenu()

    def write_second_toolbar(self, screen):
        """
        When inside functions, show signature.
        """
        if self.commandline.input_processor.input_mode == InputMode.INCREMENTAL_SEARCH:
            screen.write_highlighted(list(self.isearch_prompt))
        elif self.commandline.input_processor.arg is not None:
            screen.write_highlighted(list(self.arg_prompt))
        elif self.line.validation_error:
            screen.write_highlighted(list(self._get_error_tokens()))
        elif self.commandline.autocompletion_style == AutoCompletionStyle.HORIZONTAL_MENU and \
                        self.line.complete_state and \
                        self.commandline.input_processor.input_mode == InputMode.COMPLETE:
            HorizontalCompletionMenu().write(screen, None, self.line.complete_state)
        else:
            screen.write_highlighted(list(self._get_signature_tokens()))

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

    def create_left_input_margin(self, screen, row, is_new_line):
        prompt_width = len(TokenList(self.tokens_before_input))

        if is_new_line:
            text = '%i. ' % row
        else:
            text = ''

        text = ' ' * (prompt_width - len(text)) + text

        screen.write_highlighted([
            (Token.Prompt.LineNumber, text)
        ])

    def _get_bottom_position(self, screen, last_screen_height):
        # Draw the menu at the bottom position.
        return max(self.min_height - 2, screen.current_height, last_screen_height - 2) - 1

    def _print_tildes(self, screen):
        """
        Print tildes in the left margin between the last input line and the
        toolbars.
        """
        last_char_y, last_char_x = screen._cursor_mappings[len(self.line.document.text)]

        # Fill space with tildes
        for y in range(last_char_y + 1, screen.current_height - 2):
            screen.write_at_pos(y, 1, '~', Token.Leftmargin.Tilde)

    def write_to_screen(self, screen, last_screen_height, accept=False, abort=False):
        self.write_before_input(screen)
        self.write_input(screen)

        if not (accept or abort):
            y = self._get_bottom_position(screen, last_screen_height)
            self.write_menus(screen) # XXX: menu should be able to cover the second toolbar.
            y2 = self._get_bottom_position(screen, last_screen_height)
            y = max(y, y2 - 1)


            screen._y, screen._x = y + 1, 0
            self.write_second_toolbar(screen)

            screen._y, screen._x = y + 2, 0
            self.write_toolbar(screen)

            self._print_tildes(screen)

    def write_toolbar(self, screen):
        TB = Token.Toolbar
        mode = self.commandline.input_processor.input_mode

        result = TokenList()
        append = result.append

        append((TB, ' '))

        # Mode
        if mode == InputMode.INCREMENTAL_SEARCH:
            append((TB.Mode, '(SEARCH)'))
            append((TB, '   '))
        elif self.commandline.vi_mode:
            if mode == InputMode.VI_NAVIGATION:
                append((TB.Mode, '(NAV)'))
                append((TB, '      '))
            elif mode == InputMode.VI_INSERT:
                append((TB.Mode, '(INSERT)'))
                append((TB, '   '))
            elif mode == InputMode.VI_REPLACE:
                append((TB.Mode, '(REPLACE)'))
                append((TB, '  '))
            elif mode == InputMode.COMPLETE:
                append((TB.Mode, '(COMPLETE)'))
                append((TB, ' '))

#            if self.commandline._input_processor.is_recording_macro:
#                append((TB.Mode, 'recording'))
#                append((TB, ' '))

        else:
            append((TB.Mode, '(emacs)'))
            append((TB, ' '))

        # Position in history.
        append((TB, '%i/%i ' % (self.line._working_index + 1, len(self.line._working_lines))))

        # Shortcuts.
        if mode == InputMode.INCREMENTAL_SEARCH:
            append((TB, '[Ctrl-G] Cancel search [Enter] Go to this position.'))
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
            append((TB.PythonVersion, '%s %i.%i.%i' % (platform.python_implementation(),
                                version.major, version.minor, version.micro)))

        # Adjust toolbar width.
        if len(result) > screen.size.columns:
            # Trim toolbar
            result = result[:screen.size.columns - 3]
            result.append((TB, ' > '))
        else:
            # Extend toolbar until the page width.
            result.append((TB, ' ' * (screen.size.columns - len(result))))

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
    def __init__(self, text, start_position, jedi_completion):
        super(PythonCompletion, self).__init__(text, start_position)
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
                yield PythonCompletion(c.name, len(c.complete) - len(c.name), c)


class PythonCommandLineInterface(CommandLineInterface):
    line_factory = PythonLine
    prompt_factory = PythonPrompt

    def __init__(self, globals=None, locals=None, vi_mode=False, stdin=None, stdout=None, history_filename=None,
                    style=PythonStyle, autocompletion_style=AutoCompletionStyle.POPUP_MENU):

        self.globals = globals or {}
        self.locals = locals or {}
        self.history_filename = history_filename
        self.style = style
        self.autocompletion_style = autocompletion_style

        self.vi_mode = vi_mode
        self.get_signatures_thread_running = False

        #: Incremeting integer counting the current statement.
        self.current_statement_index = 1

        super(PythonCommandLineInterface, self).__init__(stdin=stdin, stdout=stdout)

    def history_factory(self):
        if self.history_filename:
            return FileHistory(self.history_filename)
        else:
            return History()

    @property
    def key_bindings_factories(self):
        if self.vi_mode:
            return [vi_bindings, python_bindings]
        else:
            return [emacs_bindings, python_bindings]

    def code_factory(self, document):
        # The `PythonCode` needs a reference back to this class in order to do
        # autocompletion on the globals/locals.
        return PythonCode(document, self.globals, self.locals)

    def on_input_timeout(self):
        """
        When there is no input activity,
        in another thread, get the signature of the current code.
        """
        # Never run multiple get-signature threads.
        if self.get_signatures_thread_running:
            return
        self.get_signatures_thread_running = True

        code_obj = self.line.create_code_obj()

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
            if self.line.text == code_obj.text:
                self.line.signatures = signatures
                self.request_redraw()
            else:
                self.on_input_timeout()

        self.run_in_executor(run)
