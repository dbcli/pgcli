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
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import FileHistory, History
from prompt_toolkit.key_binding.bindings.vi import ViStateFilter
from prompt_toolkit.key_binding.manager import KeyBindingManager, ViModeEnabled
from prompt_toolkit.key_binding.vi_state import InputMode
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.margins import LeftMarginWithLineNumbers
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import BracketsMismatchProcessor
from prompt_toolkit.layout.toolbars import CompletionsToolbar, ArgToolbar, SearchToolbar, ValidationToolbar, SystemToolbar
from prompt_toolkit.layout.toolbars import Toolbar
from prompt_toolkit.selection import SelectionType
from prompt_toolkit.validation import Validator, ValidationError

from .regular_languages.compiler import compile as compile_grammar
from .regular_languages.completion import GrammarCompleter
from .completers import PathCompleter

import prompt_toolkit.filters as filters

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


def load_python_bindings(key_bindings_manager, settings, always_multiline=False):
    """
    Custom key bindings.
    """
    handle = key_bindings_manager.registry.add_binding
    has_selection = filters.HasSelection()

    @handle(Keys.F4)
    def _(event):
        """
        Toggle between Vi and Emacs mode.
        """
        key_bindings_manager.enable_vi_mode = not key_bindings_manager.enable_vi_mode

    @handle(Keys.F6)
    def _(event):
        """
        Enable/Disable paste mode.
        """
        settings.paste_mode = not settings.paste_mode

    @handle(Keys.F7)
    def _(event):
        """
        Enable/Disable multiline mode.
        """
        settings.currently_multiline = not settings.currently_multiline

    @handle(Keys.F2, filter=filters.HasFocus('default') & ~has_selection)
    def _(event):
        """
        Merge the previous entry from the history on top.
        """
        buffer = event.cli.buffers['default']

        buffer.text = buffer._working_lines[buffer.working_index - 1] + '\n' + buffer.text
        buffer._working_lines = buffer._working_lines[:buffer.working_index - 1] + buffer._working_lines[buffer.working_index:]
        buffer.working_index -= 1

    @handle(Keys.Tab, filter= ~has_selection)
    def _(event):
        """
        When the 'tab' key is pressed with only whitespace character before the
        cursor, do autocompletion. Otherwise, insert indentation.
        """
        buffer = event.cli.buffers['default']
        current_char = buffer.document.current_line_before_cursor

        if not current_char or current_char.isspace():
            buffer.insert_text('    ')
        else:
            buffer.complete_next()

    @handle(Keys.ControlJ, filter= ~has_selection &
                                   ~(ViModeEnabled(key_bindings_manager) &
                                     ViStateFilter(key_bindings_manager.vi_state, InputMode.NAVIGATION)) &
                                   filters.HasFocus('default') & filters.IsMultiline())
    def _(event):
        """
        Auto indent after newline/Enter.
        (When not in Vi navigaton mode, and when multiline is enabled.)
        """
        buffer = event.current_buffer

        if settings.paste_mode:
            buffer.insert_text('\n')
        else:
            auto_newline(buffer)


def auto_newline(buffer):
    r"""
    Insert \n at the cursor position. Also add necessary padding.
    """
    insert_text = buffer.insert_text

    if buffer.document.current_line_after_cursor:
        insert_text('\n')
    else:
        # Go to new line, but also add indentation.
        current_line = buffer.document.current_line_before_cursor.rstrip()
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


class PythonBuffer(Buffer):
    """
    Custom `Buffer` class with some helper functions.
    """
    def reset(self, *a, **kw):
        super(PythonBuffer, self).reset(*a, **kw)

        # Code signatures. (This is set asynchronously after a timeout.)
        self.signatures = []


_multiline_string_delims = re.compile('''[']{3}|["]{3}''')


def document_is_multiline_python(document):
    """
    Determine whether this is a multiline Python document.
    """
    def ends_in_multiline_string():
        """
        ``True`` if we're inside a multiline string at the end of the text.
        """
        delims = _multiline_string_delims.findall(document.text)
        opening = None
        for delim in delims:
            if opening is None:
                opening = delim
            elif delim == opening:
                opening = None
        return bool(opening)

    if '\n' in document.text or ends_in_multiline_string():
        return True

    # If we just typed a colon, or still have open brackets, always insert a real newline.
    if document.text_before_cursor.rstrip()[-1:] == ':' or \
            (document.is_cursor_at_the_end and
             _has_unclosed_brackets(document.text_before_cursor)) or \
            document.text.startswith('@'):
        return True

    # If the character before the cursor is a backslash (line continuation
    # char), insert a new line.
    elif document.text_before_cursor[-1:] == '\\':
        return True

    return False


class SignatureToolbar(Toolbar):
    def is_visible(self, cli):
        return super(SignatureToolbar, self).is_visible(cli) and bool(cli.buffers['default'].signatures)

    def get_tokens(self, cli, width):
        result = []
        append = result.append
        Signature = Token.Toolbar.Signature

        if cli.buffers['default'].signatures:
            sig = cli.buffers['default'].signatures[0]  # Always take the first one.

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


def get_inputmode_tokens(token, key_bindings_manager, cli):
    """
    Return current input mode as a list of (token, text) tuples for use in a
    toolbar.

    :param vi_mode: (bool) True when vi mode is enabled.
    :param cli: `CommandLineInterface` instance.
    """
    mode = key_bindings_manager.vi_state.input_mode
    result = []
    append = result.append

    # InputMode
    if key_bindings_manager.enable_vi_mode:
        if bool(cli.buffers['default'].selection_state):
            if cli.buffers['default'].selection_state.type == SelectionType.LINES:
                append((token.InputMode, '[F4] Vi (VISUAL LINE)'))
                append((token, ' '))
            elif cli.buffers['default'].selection_state.type == SelectionType.CHARACTERS:
                append((token.InputMode, '[F4] Vi (VISUAL)'))
                append((token, ' '))
        elif mode == InputMode.INSERT:
            append((token.InputMode, '[F4] Vi (INSERT)'))
            append((token, '  '))
        elif mode == InputMode.NAVIGATION:
            append((token.InputMode, '[F4] Vi (NAV)'))
            append((token, '     '))
        elif mode == InputMode.REPLACE:
            append((token.InputMode, '[F4] Vi (REPLACE)'))
            append((token, ' '))
    else:
        append((token.InputMode, '[F4] Emacs'))
        append((token, ' '))

    return result


class PythonToolbar(Toolbar):
    def __init__(self, key_bindings_manager, settings, token=None):
        self.key_bindings_manager = key_bindings_manager
        self.settings = settings

        token = token or Token.Toolbar.Status
        super(PythonToolbar, self).__init__(token=token)

    def get_tokens(self, cli, width):
        TB = self.token
        result = []
        append = result.append

        append((TB, ' '))
        result.extend(get_inputmode_tokens(TB, self.key_bindings_manager, cli))

        # Position in history.
        append((TB, '%i/%i ' % (cli.buffers['default'].working_index + 1, len(cli.buffers['default']._working_lines))))

        # Shortcuts.
        if not self.key_bindings_manager.enable_vi_mode and cli.focus_stack.current == 'search':
            append((TB, '[Ctrl-G] Cancel search [Enter] Go to this position.'))
        elif bool(cli.buffers['default'].selection_state) and not self.key_bindings_manager.enable_vi_mode:
            # Emacs cut/copy keys.
            append((TB, '[Ctrl-W] Cut [Meta-W] Copy [Ctrl-Y] Paste [Ctrl-G] Cancel'))
        else:
            append((TB.On, '[F2] Merge history '))
            if self.settings.paste_mode:
                append((TB.On, '[F6] Paste mode (on)  '))
            else:
                append((TB.Off, '[F6] Paste mode (off) '))

            if not self.settings.always_multiline:
                if self.settings.currently_multiline or \
                        document_is_multiline_python(cli.buffers['default'].document):
                    append((TB.On, '[F7] Multiline (on)'))
                else:
                    append((TB.Off, '[F7] Multiline (off)'))

            if cli.buffers['default'].is_multiline:
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
            index = document.translate_row_col_to_index(e.lineno - 1,  (e.offset or 1) - 1)
            raise ValidationError(index, 'Syntax Error')
        except TypeError as e:
            # e.g. "compile() expected string without null bytes"
            raise ValidationError(0, str(e))


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
    except AttributeError:
        # Workaround for #65: https://github.com/jonathanslenders/python-prompt-toolkit/issues/65
        # See also: https://github.com/davidhalter/jedi/issues/508
        return None
    except IndexError:
        # Workaround Jedi issue #514: for https://github.com/davidhalter/jedi/issues/514
        return None


class PythonCompleter(Completer):
    def __init__(self, get_globals, get_locals):
        super(PythonCompleter, self).__init__()

        self.get_globals = get_globals
        self.get_locals = get_locals

        self._path_completer_grammar, self._path_completer = self._create_path_completer()

    def _create_path_completer(self):
        def unwrapper(text):
            return re.sub(r'\\(.)', r'\1', text)

        def single_quoted_wrapper(text):
            return text.replace('\\', '\\\\').replace("'", "\\'")

        def double_quoted_wrapper(text):
            return text.replace('\\', '\\\\').replace('"', '\\"')

        grammar = r"""
                # Text before the current string.
                (
                    [^'"#]            |  # Not quoted characters.
                    '''.*'''          |  # Inside single quoted triple strings
                    "" ".*"" "        |  # Inside double quoted triple strings
                    \#[^\n]*          |  # Comment.
                    "([^"\\]|\\.)*"   |  # Inside double quoted strings.
                    '([^'\\]|\\.)*'      # Inside single quoted strings.
                )*
                # The current string that we're completing.
                (
                    ' (?P<var1>([^\n'\\]|\\.)*) |  # Inside a single quoted string.
                    " (?P<var2>([^\n"\\]|\\.)*)    # Inside a double quoted string.
                )
        """

        g = compile_grammar(grammar,
            escape_funcs={
                'var1': single_quoted_wrapper,
                'var2': double_quoted_wrapper,
            },
            unescape_funcs={
                'var1': unwrapper,
                'var2': unwrapper,
            })
        return g, GrammarCompleter(g, {
                'var1': PathCompleter(),
                'var2': PathCompleter(),
            })

    def _complete_path_while_typing(self, document):
        char_before_cursor = document.char_before_cursor
        return document.text and (
            char_before_cursor.isalnum() or char_before_cursor in '/.~')

    def _complete_python_while_typing(self, document):
        char_before_cursor = document.char_before_cursor
        return document.text and (
            char_before_cursor.isalnum() or char_before_cursor in '_.')

    def get_completions(self, document, complete_event):
        """
        Get Python completions.
        """
        # Do Path completions
        if complete_event.completion_requested or self._complete_path_while_typing(document):
            for c in self._path_completer.get_completions(document, complete_event):
                yield c

        # If we are inside a string, Don't do Jedi completion.
        if self._path_completer_grammar.match(document.text):
            return

        # Do Jedi Python completions.
        if complete_event.completion_requested or self._complete_python_while_typing(document):
            script = get_jedi_script_from_document(document, self.get_locals(), self.get_globals())

            if script:
                try:
                    completions = script.completions()
                except TypeError:
                    # Issue #9: bad syntax causes completions() to fail in jedi.
                    # https://github.com/jonathanslenders/python-prompt-toolkit/issues/9
                    pass
                except UnicodeDecodeError:
                    # Issue #43: UnicodeDecodeError on OpenBSD
                    # https://github.com/jonathanslenders/python-prompt-toolkit/issues/43
                    pass
                except AttributeError:
                    # Jedi issue #513: https://github.com/davidhalter/jedi/issues/513
                    pass
                else:
                    for c in completions:
                        yield Completion(c.name_with_symbols, len(c.complete) - len(c.name_with_symbols),
                                         display=c.name_with_symbols)


class PythonCLISettings(object):
    """
    Settings for the Python REPL which can change at runtime.
    """
    def __init__(self,
                 always_multiline=False,
                 paste_mode=False):
        self.always_multiline = always_multiline
        self.currently_multiline = False

        #: Boolean `paste` flag. If True, don't insert whitespace after a
        #: newline.
        self.paste_mode = paste_mode


class PythonCommandLineInterface(CommandLineInterface):
    def __init__(self,
                 get_globals=None, get_locals=None,
                 stdin=None, stdout=None,
                 vi_mode=False, history_filename=None,
                 style=PythonStyle,
                 autocompletion_style=AutoCompletionStyle.POPUP_MENU,
                 always_multiline=False,

                 # For internal use.
                 _left_margin=None,
                 _completer=None,
                 _validator=None):

        self.settings = PythonCLISettings(always_multiline=always_multiline)

        self.get_globals = get_globals or (lambda: {})
        self.get_locals = get_locals or self.get_globals

        left_margin = _left_margin or PythonLeftMargin()
        self.completer = _completer or PythonCompleter(self.get_globals, self.get_locals)
        validator = _validator or PythonValidator()

        if history_filename:
            history = FileHistory(history_filename)
        else:
            history = History()

        # Use a KeyBindingManager for loading the key bindings.
        self.key_bindings_manager = KeyBindingManager(enable_vi_mode=vi_mode, enable_system_prompt=True)
        load_python_bindings(self.key_bindings_manager, self.settings, always_multiline=always_multiline)

        layout = Layout(
            input_processors=[BracketsMismatchProcessor()],
            min_height=7,
            lexer=PythonLexer,
            left_margin=left_margin,
            menus=[CompletionsMenu()] if autocompletion_style == AutoCompletionStyle.POPUP_MENU else [],
            bottom_toolbars=[
                ArgToolbar(),
                SignatureToolbar(),
                SearchToolbar(),
                SystemToolbar(),
                ValidationToolbar(),
            ] +
            ([CompletionsToolbar()] if autocompletion_style == AutoCompletionStyle.HORIZONTAL_MENU else []) +
            [
                PythonToolbar(self.key_bindings_manager, self.settings),
            ],
            show_tildes=True)

        def is_buffer_multiline(document):
            return (self.settings.paste_mode or
                    self.settings.always_multiline or
                    self.settings.currently_multiline or
                    document_is_multiline_python(document))

        buffer=PythonBuffer(
                        is_multiline=is_buffer_multiline,
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
            key_bindings_registry=self.key_bindings_manager.registry,
            buffer=buffer,
            create_async_autocompleters=True)

        def on_input_timeout():
            """
            When there is no input activity,
            in another thread, get the signature of the current code.
            """
            if self.focus_stack.current != 'default':
                return

            # Never run multiple get-signature threads.
            if self.get_signatures_thread_running:
                return
            self.get_signatures_thread_running = True

            document = self.buffers['default'].document

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
                if self.buffers['default'].text == document.text:
                    self.buffers['default'].signatures = signatures
                    self.request_redraw()
                else:
                    on_input_timeout()

            self.run_in_executor(run)

        self.onInputTimeout += on_input_timeout
        self.onReset += self.key_bindings_manager.reset
