"""

::

    from prompt_toolkit.contrib.python_import import PythonCommandLineInterface

    cli = PythonCommandLineInterface()
    cli.read_input()
"""
from __future__ import unicode_literals

from pygments.lexers import PythonLexer
from pygments.style import Style
from pygments.token import Keyword, Operator, Number, Name, Error, Comment, Token, String

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.enums import InputMode
from prompt_toolkit.history import FileHistory, History
from prompt_toolkit.key_bindings.emacs import emacs_bindings
from prompt_toolkit.key_bindings.vi import vi_bindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.menus import CompletionMenu
from prompt_toolkit.layout.processors import BracketsMismatchProcessor
from prompt_toolkit.layout.toolbars import CompletionToolbar, ArgToolbar, SearchToolbar, ValidationToolbar, SystemToolbar
from prompt_toolkit.layout.toolbars import Toolbar
from prompt_toolkit.layout.utils import TokenList
from prompt_toolkit.line import Line
from prompt_toolkit.selection import SelectionType
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.layout.margins import LeftMarginWithLineNumbers

import jedi
import platform
import re
import sys


__all__ = (
    'PythonCommandLineInterface',
    'AutoCompletionStyle',
)


_identifier_re = re.compile(r'[a-zA-Z_0-9_\.]+')


class AutoCompletionStyle:
    #: tab/double-tab completion
    # TRADITIONAL = 'traditional'  # TODO: not implemented yet.

    #: Pop-up
    POPUP_MENU = 'popup-menu'

    #: Horizontal list
    HORIZONTAL_MENU = 'horizontal-menu'

    #: No visualisation
    NONE = 'none'


class PythonStyle(Style):
    background_color = None
    styles = {
        # Build-ins from the Pygments lexer.
        Comment:                                      '#0000dd',
        Error:                                        '#000000 bg:#ff8888',
        Keyword:                                      '#ee00ee',
        Name.Decorator:                               '#aa22ff',
        Name.Namespace:                               '#008800 underline',
        Name:                                         '#008800',
        Number:                                       '#ff0000',
        Operator:                                     '#ff6666 bold',
        String:                                       '#ba4444 bold',

        # Highlighting of search matches in document.
        Token.SearchMatch:                            '#ffffff bg:#4444aa',
        Token.SearchMatch.Current:                    '#ffffff bg:#44aa44',

        # Highlighting of select text in document.
        Token.SelectedText:                           '#ffffff bg:#6666aa',

        # (Python) Prompt: "In [1]:"
        Token.Prompt:                                 'bold #008800',

        # Line numbers.
        Token.Layout.LeftMargin:                      '#aa6666',

        # Search toolbar.
        Token.Toolbar.Search:                         '#22aaaa noinherit',
        Token.Toolbar.Search.Text:                    'noinherit',
        Token.Toolbar.Search.Text.NoMatch:            'bg:#aa4444 #ffffff',

        # System toolbar
        Token.Toolbar.System.Prefix:                  '#22aaaa noinherit',

        # "arg" toolbar.
        Token.Toolbar.Arg:                            '#22aaaa noinherit',
        Token.Toolbar.Arg.Text:                       'noinherit',

        # Signature toolbar.
        Token.Toolbar.Signature:                      '#888888',
        Token.Toolbar.Signature.CurrentName:          'bold underline #888888',
        Token.Toolbar.Signature.Operator:             'bold #888888',

        # Validation toolbar.
        Token.Toolbar.Validation:                     'bg:#440000 #aaaaaa',

        # Status toolbar.
        Token.Toolbar.Status:                         'bg:#222222 #aaaaaa',
        Token.Toolbar.Status.InputMode:               'bg:#222222 #ffffaa',
        Token.Toolbar.Status.Off:                     'bg:#222222 #888888',
        Token.Toolbar.Status.On:                      'bg:#222222 #ffffff',
        Token.Toolbar.Status.PythonVersion:           'bg:#222222 #ffffff bold',

        # Completer toolbar.
        Token.Toolbar.Completions:                    'noinherit',
        Token.Toolbar.Completions.Arrow:              'bold #888888',
        Token.Toolbar.Completions.Completion:         '#888888 noinherit',
        Token.Toolbar.Completions.Completion.Current: 'bold noinherit',

        # Completer menu.
        Token.Menu.Completions.Completion:            'bg:#888888 #ffffbb',
        Token.Menu.Completions.Completion.Current:    'bg:#dddddd #000000',
        Token.Menu.Completions.Meta:                  'bg:#888888 #cccccc',
        Token.Menu.Completions.Meta.Current:          'bg:#bbbbbb #000000',
        Token.Menu.Completions.ProgressBar:           'bg:#aaaaaa',
        Token.Menu.Completions.ProgressButton:        'bg:#000000',

        # When Control-C has been pressed. Grayed.
        Token.Aborted:                                '#888888',

        # Vi-style tildes.
        Token.Leftmargin.Tilde:                       '#888888',
    }


def _has_unclosed_brackets(text):
    """
    Starting at the end of the string. If we find an opening bracket
    for which we didn't had a closing one yet, return True.
    """
    stack = []

    # Ignore braces inside strings
    text = re.sub(r'''('[^']*'|"[^"]*")''', '', text)  # XXX: handle escaped quotes.!

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

    @handle(Keys.F6)
    def _(event):
        """
        Enable/Disable paste mode.
        """
        line.paste_mode = not line.paste_mode
        if line.paste_mode:
            line.is_multiline = True

    if not cli_ref().line.always_multiline:
        @handle(Keys.F7)
        def _(event):
            """
            Enable/Disable multiline mode.
            """
            line.always_multiline = not line.always_multiline

    @handle(Keys.Tab, in_mode=InputMode.INSERT)
    def _(event):
        """
        When the 'tab' key is pressed with only whitespace character before the
        cursor, do autocompletion. Otherwise, insert indentation.
        """
        current_char = line.document.current_line_before_cursor
        if not current_char or current_char.isspace():
            line.insert_text('    ')
        else:
            line.complete_next()


class PythonLine(Line):
    """
    Custom `Line` class with some helper functions.
    """
    def __init__(self, always_multiline, *a, **kw):
        self.always_multiline = always_multiline
        super(PythonLine, self).__init__(*a, **kw)

    def reset(self, *a, **kw):
        super(PythonLine, self).reset(*a, **kw)

        #: Boolean `paste` flag. If True, don't insert whitespace after a
        #: newline.
        self.paste_mode = False

        #: Boolean `multiline` flag. If True, [Enter] will always insert a
        #: newline, and it is required to use [Meta+Enter] execute commands.
        self.is_multiline = self.always_multiline

        # Code signatures. (This is set asynchronously after a timeout.)
        self.signatures = []

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

    @property
    def is_multiline(self):
        """
        Dynamically determine whether we're in multiline mode.
        """
        if self.always_multiline or self.paste_mode or '\n' in self.text:
            return True

        # If we just typed a colon, or still have open brackets, always insert a real newline.
        if self.document.text_before_cursor.rstrip()[-1:] == ':' or \
                (self.document.is_cursor_at_the_end and
                 _has_unclosed_brackets(self.document.text_before_cursor)) or \
                self.text.startswith('@'):
            return True

        # If the character before the cursor is a backslash (line continuation
        # char), insert a new line.
        elif self.document.text_before_cursor[-1:] == '\\':
            return True

        return False

    @is_multiline.setter
    def is_multiline(self, value):
        """ Ignore setter. """
        pass


class SignatureToolbar(Toolbar):
    def is_visible(self, cli):
        return super(SignatureToolbar, self).is_visible(cli) and bool(cli.line.signatures)

    def get_tokens(self, cli, width):
        result = []
        append = result.append
        Signature = Token.Toolbar.Signature

        if cli.line.signatures:
            sig = cli.line.signatures[0]  # Always take the first one.

            append((Token, '           '))
            try:
                append((Signature, sig.full_name))
            except IndexError:
                # Workaround for #37: https://github.com/jonathanslenders/python-prompt-toolkit/issues/37
                # See also: https://github.com/davidhalter/jedi/issues/490
                return []

            append((Signature.Operator, '('))

            for i, p in enumerate(sig.params):
                if i == sig.index:
                    append((Signature.CurrentName, str(p.name)))
                else:
                    append((Signature, str(p.name)))
                append((Signature.Operator, ', '))

            if sig.params:
                # Pop last comma
                result.pop()

            append((Signature.Operator, ')'))
        return result


class PythonToolbar(Toolbar):
    def __init__(self, vi_mode, token=None):
        token = token or Token.Toolbar.Status
        self.vi_mode = vi_mode
        super(PythonToolbar, self).__init__(token=token)

    def get_tokens(self, cli, width):
        TB = self.token
        mode = cli.input_processor.input_mode

        result = TokenList()
        append = result.append

        append((TB, ' '))

        # InputMode
        if mode == InputMode.INCREMENTAL_SEARCH:
            append((TB.InputMode, '(SEARCH)'))
            append((TB, '   '))
        elif self.vi_mode:
            if mode == InputMode.INSERT:
                append((TB.InputMode, '(INSERT)'))
                append((TB, '   '))
            elif mode == InputMode.VI_SEARCH:
                append((TB.InputMode, '(SEARCH)'))
                append((TB, '   '))
            elif mode == InputMode.VI_NAVIGATION:
                append((TB.InputMode, '(NAV)'))
                append((TB, '      '))
            elif mode == InputMode.VI_REPLACE:
                append((TB.InputMode, '(REPLACE)'))
                append((TB, '  '))
            elif mode == InputMode.SELECTION and cli.line.selection_state:
                if cli.line.selection_state.type == SelectionType.LINES:
                    append((TB.InputMode, '(VISUAL LINE)'))
                    append((TB, ' '))
                elif cli.line.selection_state.type == SelectionType.CHARACTERS:
                    append((TB.InputMode, '(VISUAL)'))
                    append((TB, ' '))

        else:
            append((TB.InputMode, '(emacs)'))
            append((TB, ' '))

        # Position in history.
        append((TB, '%i/%i ' % (cli.line.working_index + 1, len(cli.line._working_lines))))

        # Shortcuts.
        if mode == InputMode.INCREMENTAL_SEARCH:
            append((TB, '[Ctrl-G] Cancel search [Enter] Go to this position.'))
        elif mode == InputMode.SELECTION and not self.vi_mode:
            # Emacs cut/copy keys.
            append((TB, '[Ctrl-W] Cut [Meta-W] Copy [Ctrl-Y] Paste [Ctrl-G] Cancel'))
        else:
            if cli.line.paste_mode:
                append((TB.On, '[F6] Paste mode (on)  '))
            else:
                append((TB.Off, '[F6] Paste mode (off) '))

            if not cli.always_multiline:
                if cli.line.is_multiline:
                    append((TB.On, '[F7] Multiline (on)'))
                else:
                    append((TB.Off, '[F7] Multiline (off)'))

            if cli.line.is_multiline:
                append((TB, ' [Meta+Enter] Execute'))

            # Python version
            version = sys.version_info
            append((TB, ' - '))
            append((TB.PythonVersion, '%s %i.%i.%i' % (platform.python_implementation(),
                   version[0], version[1], version[2])))

        # Adjust toolbar width.
        if len(result) > width:
            # Trim toolbar
            result = result[:width - 3]
            result.append((TB, ' > '))
        else:
            # Extend toolbar until the page width.
            result.append((TB, ' ' * (width - len(result))))

        return result


class PythonLeftMargin(LeftMarginWithLineNumbers):
    def width(self, cli):
        return len('In [%s]: ' % cli.current_statement_index)

    def current_statement_index(self, cli):
        return cli.current_statement_index

    def write(self, cli, screen, y, line_number):
        if y == 0:
            screen.write_highlighted([
                (Token.Prompt, 'In [%s]: ' % self.current_statement_index(cli))
            ])
        else:
            super(PythonLeftMargin, self).write(cli, screen, y, line_number)


class PythonValidator(Validator):
    def validate(self, document):
        """
        Check input for Python syntax errors.
        """
        try:
            compile(document.text, '<input>', 'exec')
        except SyntaxError as e:
            # Note, the 'or 1' for offset is required because Python 2.7
            # gives `None` as offset in case of '4=4' as input. (Looks like
            # fixed in Python 3.)
            raise ValidationError(e.lineno - 1, (e.offset or 1) - 1, 'Syntax Error')
        except TypeError as e:
            # e.g. "compile() expected string without null bytes"
            raise ValidationError(0, 0, str(e))


def get_jedi_script_from_document(document, locals, globals):
    try:
        return jedi.Interpreter(
            document.text,
            column=document.cursor_position_col,
            line=document.cursor_position_row + 1,
            path='input-text',
            namespaces=[locals, globals])

    except jedi.common.MultiLevelStopIteration:
        # This happens when the document is just a backslash.
        return None
    except ValueError:
        # Invalid cursor position.
        # ValueError('`column` parameter is not in a valid range.')
        return None


class PythonCompleter(Completer):
    def __init__(self, get_globals, get_locals):
        super(PythonCompleter, self).__init__()

        self.get_globals = get_globals
        self.get_locals = get_locals

    def get_completions(self, document):
        """ Ask jedi to complete. """
        script = get_jedi_script_from_document(document, self.get_locals(), self.get_globals())

        if script:
            try:
                completions = script.completions()
            except TypeError:
                # Issue #9: bad syntax causes completions() to fail in jedi.
                # https://github.com/jonathanslenders/python-prompt-toolkit/issues/9
                pass
            else:
                for c in completions:
                    yield Completion(c.name_with_symbols, len(c.complete) - len(c.name_with_symbols),
                                     display=c.name_with_symbols)


class PythonCommandLineInterface(CommandLineInterface):
    def __init__(self,
                 get_globals=None, get_locals=None,
                 stdin=None, stdout=None,
                 vi_mode=False, history_filename=None,
                 style=PythonStyle,
                 autocompletion_style=AutoCompletionStyle.POPUP_MENU,
                 always_multiline=False,

                 # For internal use.
                 _completer=None,
                 _validator=None):

        self.get_globals = get_globals or (lambda: {})
        self.get_locals = get_locals or self.get_globals
        self.always_multiline = always_multiline
        self.autocompletion_style = autocompletion_style

        self.completer = _completer or PythonCompleter(self.get_globals, self.get_locals)
        validator = _validator or PythonValidator()

        layout = Layout(
            input_processors=[BracketsMismatchProcessor()],
            min_height=7,
            lexer=PythonLexer,
            left_margin=PythonLeftMargin(),
            menus=[CompletionMenu()] if autocompletion_style == AutoCompletionStyle.POPUP_MENU else [],
            bottom_toolbars=[
                ArgToolbar(),
                SignatureToolbar(),
                SearchToolbar(),
                SystemToolbar(),
                ValidationToolbar(),
            ] +
            ([CompletionToolbar()] if autocompletion_style == AutoCompletionStyle.HORIZONTAL_MENU else []) +
            [
                PythonToolbar(vi_mode=vi_mode),
            ],
            show_tildes=True)

        if history_filename:
            history = FileHistory(history_filename)
        else:
            history = History()

        if vi_mode:
            key_binding_factories = [vi_bindings, python_bindings]
        else:
            key_binding_factories = [emacs_bindings, python_bindings]

        line=PythonLine(always_multiline=always_multiline,
                        tempfile_suffix='.py',
                        history=history,
                        completer=self.completer,
                        validator=validator)

        #: Incremeting integer counting the current statement.
        self.current_statement_index = 1

        self.get_signatures_thread_running = False

        super(PythonCommandLineInterface, self).__init__(
            layout=layout,
            style=style,
            key_binding_factories=key_binding_factories,
            line=line,
            create_async_autocompleters=True)

        def on_input_timeout():
            """
            When there is no input activity,
            in another thread, get the signature of the current code.
            """
            # Never run multiple get-signature threads.
            if self.get_signatures_thread_running:
                return
            self.get_signatures_thread_running = True

            document = self.line.document

            def run():
                script = get_jedi_script_from_document(document, self.get_locals(), self.get_globals())

                # Show signatures in help text.
                if script:
                    try:
                        signatures = script.call_signatures()
                    except ValueError:
                        # e.g. in case of an invalid \\x escape.
                        signatures = []
                    except Exception:
                        # Sometimes we still get an exception (TypeError), because
                        # of probably bugs in jedi. We can silence them.
                        # See: https://github.com/davidhalter/jedi/issues/492
                        signatures = []
                else:
                    signatures = []

                self.get_signatures_thread_running = False

                # Set signatures and redraw if the text didn't change in the
                # meantime. Otherwise request new signatures.
                if self.line.text == document.text:
                    self.line.signatures = signatures
                    self.request_redraw()
                else:
                    on_input_timeout()

            self.run_in_executor(run)

        self.onInputTimeout += on_input_timeout
