"""
CommandLineInterface for reading Python input.
This can be used for creation of Python REPLs.

::

    from prompt_toolkit.contrib.python_import import PythonCommandLineInterface

    python_interface = PythonCommandLineInterface()
    python_interface.cli.read_input()
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
from prompt_toolkit.layout import Window, HSplit, VSplit, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl, TokenListControl, FillControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.screen import Char
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import BracketsMismatchProcessor
from prompt_toolkit.layout.toolbars import CompletionsToolbar, ArgToolbar, SearchToolbar, ValidationToolbar, SystemToolbar, TokenListToolbar
from prompt_toolkit.layout.utils import token_list_width
from prompt_toolkit.selection import SelectionType
from prompt_toolkit.validation import Validator, ValidationError
from prompt_toolkit.filters import Filter, IsDone, HasFocus, HasCompletions, RendererHeightIsKnown
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding.bindings.utils import focus_next_buffer, focus_previous_buffer

from .regular_languages.compiler import compile as compile_grammar
from .regular_languages.completion import GrammarCompleter
from .completers import PathCompleter

import prompt_toolkit.filters as filters

import jedi
import platform
import re
import sys
import six


__all__ = (
    'PythonCommandLineInterface',
)


_identifier_re = re.compile(r'[a-zA-Z_0-9_\.]+')


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
        Token.Layout.Prompt:                          'bold #008800',

        # Line numbers.
        Token.LineNumber:                             '#aa6666',

        Token.Separator:                              '#bbbbbb',

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
        Token.Toolbar.Signature:                      'bg:#44bbbb #000000',
        Token.Toolbar.Signature.CurrentName:          'bg:#008888 #ffffff bold',
        Token.Toolbar.Signature.Operator:             '#000000 bold',

        Token.Docstring:                              '#888888',

        # Tab bar
        Token.TabBar:                                 '#888888 underline',
        Token.TabBar.Tab:                             'bg:#aaaaaa #444444',
        Token.TabBar.Tab.Active:                      'bg:#ffffff #000000 bold nounderline',

        # Validation toolbar.
        Token.Toolbar.Validation:                     'bg:#440000 #aaaaaa',

        # Status toolbar.
        Token.Toolbar.Status:                         'bg:#222222 #aaaaaa',
        Token.Toolbar.Status.InputMode:               'bg:#222222 #ffffaa',
        Token.Toolbar.Status.Off:                     'bg:#222222 #888888',
        Token.Toolbar.Status.On:                      'bg:#222222 #ffffff',
        Token.Toolbar.Status.PythonVersion:           'bg:#222222 #ffffff bold',

        # Completer toolbar.
        Token.Toolbar.Completions:                    'bg:#44bbbb #000000',
        Token.Toolbar.Completions.Arrow:              'bg:#44bbbb #000000 bold',
        Token.Toolbar.Completions.Completion:         'bg:#44bbbb #000000',
        Token.Toolbar.Completions.Completion.Current: 'bg:#008888 #ffffff',

        # Completer menu.
        Token.Menu.Completions.Completion:            'bg:#44bbbb #000000',
        Token.Menu.Completions.Completion.Current:    'bg:#008888 #ffffff',
        Token.Menu.Completions.Meta:                  'bg:#449999 #000000',
        Token.Menu.Completions.Meta.Current:          'bg:#00aaaa #000000',
        Token.Menu.Completions.ProgressBar:           'bg:#aaaaaa',
        Token.Menu.Completions.ProgressButton:        'bg:#000000',

        # When Control-C has been pressed. Grayed.
        Token.Aborted:                                '#888888',

        Token.Sidebar:                                'bg:#bbbbbb',
        Token.Sidebar.Shortcut:                       'bg:#bbbbbb #000011 bold',
        Token.Sidebar.Label:                          'bg:#bbbbbb #222222',
        Token.Sidebar.Status:                         'bg:#bbbbbb #000011 bold',
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


def load_python_bindings(key_bindings_manager, settings, add_buffer, close_current_buffer):
    """
    Custom key bindings.
    """
    handle = key_bindings_manager.registry.add_binding
    has_selection = filters.HasSelection()

    vi_navigation_mode = ViStateFilter(key_bindings_manager.vi_state, InputMode.NAVIGATION) & ~ filters.HasSelection()

    @handle(Keys.F2)
    def _(event):
        """
        Show/hide sidebar.
        """
        settings.show_sidebar = not settings.show_sidebar

    @handle(Keys.F3)
    def _(event):
        """
        Shange completion style.
        """
        # Toggle between combinations.
        settings.show_completions_toolbar, settings.show_completions_menu = {
            (False, False): (False, True),
            (False, True): (True, False),
            (True, False): (False, False),
        }[settings.show_completions_toolbar, settings.show_completions_menu]

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

    @handle(Keys.F8)
    def _(event):
        """
        Show/hide signature.
        """
        settings.show_signature = not settings.show_signature

    @handle(Keys.F9)
    def _(event):
        """
        Show/hide docstring window.
        """
        settings.show_docstring = not settings.show_docstring

    @handle(Keys.F10)
    def _(event):
        """
        Show/hide line numbers
        """
        settings.show_line_numbers = not settings.show_line_numbers

    @handle(Keys.F5)
    def _(event):
        """
        Show all buffers
        """
        settings.show_all_buffers = not settings.show_all_buffers

    @handle('g', 't', filter=vi_navigation_mode)
    @handle(Keys.ControlRight)
    def _(event):
        """
        Focus next tab.
        """
        focus_next_buffer(event.cli)

    @handle('g', 'T', filter=vi_navigation_mode)
    @handle(Keys.ControlLeft)
    def _(event):
        """
        Focus previous tab.
        """
        focus_previous_buffer(event.cli)

#    @handle(Keys.F5, filter=filters.HasFocus('default') & ~has_selection)  # XXX: use current tab
#    def _(event):
#        """
#        Merge the previous entry from the history on top.
#        """
#        buffer = event.cli.buffers['default']
#
#        buffer.text = buffer._working_lines[buffer.working_index - 1] + '\n' + buffer.text
#        buffer._working_lines = buffer._working_lines[:buffer.working_index - 1] + buffer._working_lines[buffer.working_index:]
#        buffer.working_index -= 1

    @handle(Keys.ControlT, filter=IsPythonBufferFocussed() & ~has_selection)
    def _(event):
        """
        Create a new Python buffer.
        """
        add_buffer()

    @handle(Keys.ControlD, filter=IsPythonBufferFocussed())
    def _(event):
        """
        Close Python buffer.
        """
        close_current_buffer()

    @handle(Keys.Tab, filter= ~has_selection)
    def _(event):
        """
        When the 'tab' key is pressed with only whitespace character before the
        cursor, do autocompletion. Otherwise, insert indentation.
        """
        buffer = event.cli.current_buffer
        current_char = buffer.document.current_line_before_cursor

        if not current_char or current_char.isspace():
            buffer.insert_text('    ')
        else:
            buffer.complete_next()

    @handle(Keys.ControlJ, filter= ~has_selection &
            ~(ViModeEnabled(key_bindings_manager) &
              ViStateFilter(key_bindings_manager.vi_state, InputMode.NAVIGATION)) &
            IsPythonBufferFocussed() & filters.IsMultiline())
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


class PythonSidebarControl(TokenListControl):
    def __init__(self, settings, key_bindings_manager):
        def get_tokens(cli):
            tokens = []
            TB = Token.Sidebar

            if key_bindings_manager.enable_vi_mode:
                mode = 'vi'
            else:
                mode = 'emacs'

            if settings.show_completions_toolbar:
                completion_style = 'toolbar'
            elif settings.show_completions_menu:
                completion_style = 'pop-up'
            else:
                completion_style = 'off'

            def append(shortcut, label, status):
                tokens.append((TB.Shortcut, ' [%s] ' % shortcut))
                tokens.append((TB.Label, '%-18s' % label))
                if status:
                    tokens.append((TB.Status, '%9s\n' % status))
                else:
                    tokens.append((TB.Label, '\n'))

            append('Ctrl-T', 'New tab', '')
            append('Ctrl-D', 'Close tab', '')
            append('Ctrl-Left/Right', 'Focus tab', '')
            append('F3', 'Completion menu', '(%s)' % completion_style)
            append('F4', 'Input mode', '(%s)' % mode)
            append('F5', 'Show all tabs', '(on)' if settings.show_all_buffers else '(off)')
#            append('F5', 'Merge from history', '')
            append('F6', 'Paste mode', '(on)' if settings.paste_mode else '(off)')
            append('F7', 'Multiline', '(always)' if settings.currently_multiline else '(auto)')
            append('F8', 'Show signature', '(on)' if settings.show_signature else '(off)')
            append('F9', 'Show docstring', '(on)' if settings.show_docstring else '(off)')
            append('F10', 'Show line numbers', '(on)' if settings.show_line_numbers else '(off)')

            return tokens

        super(PythonSidebarControl, self).__init__(get_tokens, Char(token=Token.Sidebar))


class PythonSidebar(Window):
    def __init__(self, settings, key_bindings_manager):
        super(PythonSidebar, self).__init__(
            PythonSidebarControl(settings, key_bindings_manager),
            width=LayoutDimension.exact(34),
            filter=_ShowSidebar(settings) & ~IsDone())


class SignatureControl(TokenListControl):
    def __init__(self, settings):
        def get_tokens(cli):
            result = []
            append = result.append
            Signature = Token.Toolbar.Signature

            _, python_buffer = current_python_buffer(cli, settings)

            if python_buffer.signatures:
                sig = python_buffer.signatures[0]  # Always take the first one.

                append((Signature, ' '))
                try:
                    append((Signature, sig.full_name))
                except IndexError:
                    # Workaround for #37: https://github.com/jonathanslenders/python-prompt-toolkit/issues/37
                    # See also: https://github.com/davidhalter/jedi/issues/490
                    return []

                append((Signature.Operator, '('))

                for i, p in enumerate(sig.params):
                    if i == sig.index:
                        # Note: we use `_Param.description` instead of
                        #       `_Param.name`, that way we also get the '*' before args.
                        append((Signature.CurrentName, str(p.description)))
                    else:
                        append((Signature, str(p.description)))
                    append((Signature.Operator, ', '))

                if sig.params:
                    # Pop last comma
                    result.pop()

                append((Signature.Operator, ')'))
                append((Signature, ' '))
            return result

        super(SignatureControl, self).__init__(get_tokens)


class TabsControl(TokenListControl):
    """
    Displays the list of tabs.
    """
    def __init__(self, settings):
        def get_tokens(cli):
            python_buffer_names = sorted([b for b in cli.buffers.keys() if b.startswith('python-')])

            current_name, _ = current_python_buffer(cli, settings)

            result = []
            append = result.append

            append((Token.TabBar, ' '))
            for b in python_buffer_names:
                if b == current_name:
                    append((Token.TabBar.Tab.Active, ' %s ' % b))
                else:
                    append((Token.TabBar.Tab, ' %s ' % b))
                append((Token.TabBar, ' '))

            return result

        super(TabsControl, self).__init__(get_tokens, Char(token=Token.TabBar), align_right=True)


class _ShowLineNumbersFilter(Filter):
    def __init__(self, settings, buffer_name):
        self.buffer_name = buffer_name
        self.settings = settings

    def __call__(self, cli):
        return ('\n' in cli.buffers[self.buffer_name].text and
                self.settings.show_line_numbers)


class _HasSignature(Filter):
    def __init__(self, settings):
        self.settings = settings

    def __call__(self, cli):
        _, python_buffer = current_python_buffer(cli, self.settings)
        return python_buffer is not None and bool(python_buffer.signatures)


class IsPythonBufferFocussed(Filter):
    def __call__(self, cli):
        return cli.focus_stack.current.startswith('python-')


class _ShowCompletionsToolbar(Filter):
    def __init__(self, settings):
        self.settings = settings

    def __call__(self, cli):
        return self.settings.show_completions_toolbar


class _ShowCompletionsMenu(Filter):
    def __init__(self, settings):
        self.settings = settings

    def __call__(self, cli):
        return self.settings.show_completions_menu


class _ShowSidebar(Filter):
    def __init__(self, settings):
        self.settings = settings

    def __call__(self, cli):
        return self.settings.show_sidebar


class _ShowSignature(Filter):
    def __init__(self, settings):
        self.settings = settings

    def __call__(self, cli):
        return self.settings.show_signature


class _ShowDocstring(Filter):
    def __init__(self, settings):
        self.settings = settings

    def __call__(self, cli):
        return self.settings.show_docstring


class _PythonBufferFocussed(Filter):
    """
    True when this python buffer is currently focussed, or -- in case that the
    focus is currently on a search/system buffer -- when it was the last
    focussed buffer.
    """
    def __init__(self, buffer_name, settings):
        self.buffer_name = buffer_name
        self.settings = settings

    def __call__(self, cli):
        name, buffer_instance = current_python_buffer(cli, self.settings)
        return name == self.buffer_name


class _HadMultiplePythonBuffers(Filter):
    """
    True when we had a several Python buffers at some point.
    """
    def __init__(self, settings):
        self.settings = settings

    def __call__(self, cli):
        return self.settings.buffer_index > 1


class SignatureToolbar(Window):
    def __init__(self, settings):
        super(SignatureToolbar, self).__init__(
            SignatureControl(settings),
            height=LayoutDimension.exact(1),
            filter=
                # Show only when there is a signature
                _HasSignature(settings) &
                # And there are no completions to be shown. (would cover signature pop-up.)
                (~HasCompletions() | ~_ShowCompletionsMenu(settings))
                # Signature needs to be shown.
                & _ShowSignature(settings) &
                # Not done yet.
                ~IsDone())


class TabsToolbar(Window):
    def __init__(self, settings):
        super(TabsToolbar, self).__init__(
            TabsControl(settings),
            height=LayoutDimension.exact(1),
            filter=~IsDone() & _HadMultiplePythonBuffers(settings))


class PythonPrompt(TokenListControl):
    """
    Prompt showing something like "In [1]:".
    """
    def __init__(self, settings):
        def get_tokens(cli):
            return [(Token.Layout.Prompt, 'In [%s]: ' % settings.current_statement_index)]

        super(PythonPrompt, self).__init__(get_tokens)


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

    append((token.InputMode, '[F4] '))

    # InputMode
    if key_bindings_manager.enable_vi_mode:
        if bool(cli.current_buffer.selection_state):
            if cli.current_buffer.selection_state.type == SelectionType.LINES:
                append((token.InputMode, 'Vi (VISUAL LINE)'))
                append((token, ' '))
            elif cli.current_buffer.selection_state.type == SelectionType.CHARACTERS:
                append((token.InputMode, 'Vi (VISUAL)'))
                append((token, ' '))
        elif mode == InputMode.INSERT:
            append((token.InputMode, 'Vi (INSERT)'))
            append((token, '  '))
        elif mode == InputMode.NAVIGATION:
            append((token.InputMode, 'Vi (NAV)'))
            append((token, '     '))
        elif mode == InputMode.REPLACE:
            append((token.InputMode, 'Vi (REPLACE)'))
            append((token, ' '))
    else:
        append((token.InputMode, 'Emacs'))
        append((token, ' '))

    return result


class PythonToolbar(TokenListToolbar):
    def __init__(self, key_bindings_manager, settings, token=Token.Toolbar.Status):
        def get_tokens(cli):
            _, python_buffer = current_python_buffer(cli, settings)
            if not python_buffer:
                return []

            TB = token
            result = []
            append = result.append

            append((TB, ' '))
            result.extend(get_inputmode_tokens(TB, key_bindings_manager, cli))
            append((TB, '  '))

            # Position in history.
            append((TB, '%i/%i ' % (python_buffer.working_index + 1,
                                    len(python_buffer._working_lines))))

            # Shortcuts.
            if not key_bindings_manager.enable_vi_mode and cli.focus_stack.current == 'search':
                append((TB, '[Ctrl-G] Cancel search [Enter] Go to this position.'))
            elif bool(cli.current_buffer.selection_state) and not key_bindings_manager.enable_vi_mode:
                # Emacs cut/copy keys.
                append((TB, '[Ctrl-W] Cut [Meta-W] Copy [Ctrl-Y] Paste [Ctrl-G] Cancel'))
            else:
                append((TB, '  '))

                if settings.paste_mode:
                    append((TB.On, '[F6] Paste mode (on)   '))
                else:
                    append((TB.Off, '[F6] Paste mode (off)  '))

                if python_buffer.is_multiline:
                    append((TB, ' [Meta+Enter] Execute'))

            return result

        super(PythonToolbar, self).__init__(
            get_tokens,
            default_char=Char(token=token),
            filter=~IsDone() & RendererHeightIsKnown())


class ShowSidebarButtonInfo(Window):
    def __init__(self):
        token = Token.Toolbar.Status

        version = sys.version_info
        tokens = [
            (token, ' [F2] Sidebar'),
            (token, ' - '),
            (token.PythonVersion, '%s %i.%i.%i' % (platform.python_implementation(),
                                                   version[0], version[1], version[2])),
            (token, ' '),
        ]
        width = token_list_width(tokens)

        def get_tokens(cli):
            # Python version
            return tokens

        super(ShowSidebarButtonInfo, self).__init__(
            TokenListControl(get_tokens, default_char=Char(token=token)),
            filter=~IsDone() & RendererHeightIsKnown(),
            height=LayoutDimension.exact(1),
            width=LayoutDimension.exact(width))


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
    except KeyError:
        # Workaroud for a crash when the input is "u'", the start of a unicode string.
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

        g = compile_grammar(
            grammar,
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
                except ValueError:
                    # Jedi issue: "ValueError: invalid \x escape"
                    pass
                else:
                    for c in completions:
                        yield Completion(c.name_with_symbols, len(c.complete) - len(c.name_with_symbols),
                                         display=c.name_with_symbols)


class PythonCLISettings(object):
    """
    Settings for the Python REPL which can change at runtime.
    """
    def __init__(self, paste_mode=False):
        self.currently_multiline = False
        self.show_sidebar = False
        self.show_signature = True
        self.show_docstring = True
        self.show_completions_toolbar = False
        self.show_completions_menu = True
        self.show_line_numbers = True
        self.show_all_buffers = False  # split screen otherwise.

        #: Boolean `paste` flag. If True, don't insert whitespace after a
        #: newline.
        self.paste_mode = paste_mode

        #: Incremeting integer counting the current statement.
        self.current_statement_index = 1

        #: Incrementing for tab numbers
        self.buffer_index = 0


def current_python_buffer(cli, python_settings):
    """
    Return the name of the current Python input buffer.

    Returns (name, buffer_instance) tuple.
    """
    for name in [cli.focus_stack.current, cli.focus_stack.previous]:
        if name is not None and name.startswith('python-'):
            return name, cli.buffers[name]
    return None, None


def _create_layout(buffers, settings, key_bindings_manager,
                   python_prompt_control=None, lexer=PythonLexer, extra_sidebars=None):
    D = LayoutDimension
    show_all_buffers = filters.Condition(lambda cli: settings.show_all_buffers)
    extra_sidebars = extra_sidebars or []

    def create_buffer_window(buffer_name):
        def menu_position(cli):
            """
            When there is no autocompletion menu to be shown, and we have a signature,
            set the pop-up position at `bracket_start`.
            """
            b = cli.buffers[buffer_name]

            if b.complete_state is None and b.signatures:
                row, col =  b.signatures[0].bracket_start
                index = b.document.translate_row_col_to_index(row - 1, col)
                return index

        return Window(
            BufferControl(
                buffer_name=buffer_name,
                lexer=lexer,
                show_line_numbers=_ShowLineNumbersFilter(settings, buffer_name),
                input_processors=[BracketsMismatchProcessor()],
                menu_position=menu_position,
            ),
            # As long as we're editing, prefer a minimal height of 8.
            get_height=(lambda cli: (None if cli.is_done else D(min=6))),

            # When done, show only if this was focussed.
            filter=(~IsDone() & show_all_buffers) | _PythonBufferFocussed(buffer_name, settings)
        )

    def create_buffer_window_separator(buffer_name):
        return Window(
            width=D.exact(1),
            content=FillControl('\u2502', token=Token.Separator),
            filter=~IsDone() & show_all_buffers)

    buffer_windows = []
    for b in sorted(buffers):
        if b.startswith('python-'):
            buffer_windows.append(create_buffer_window_separator(b))
            buffer_windows.append(create_buffer_window(b))

    return HSplit([
        VSplit([
            HSplit([
                TabsToolbar(settings),
                FloatContainer(
                    content=HSplit([
                        VSplit([
                            Window(
                                python_prompt_control,
                                dont_extend_width=True,
                            ),
                            VSplit(buffer_windows),
                        ]),
                    ]),
                    floats=[
                        Float(xcursor=True,
                              ycursor=True,
                              content=CompletionsMenu(
                                  max_height=12,
                                  extra_filter=_ShowCompletionsMenu(settings))),
                        Float(xcursor=True,
                              ycursor=True,
                              content=SignatureToolbar(settings))
                    ]),
                ArgToolbar(),
                SearchToolbar(),
                SystemToolbar(),
                ValidationToolbar(),
                CompletionsToolbar(extra_filter=_ShowCompletionsToolbar(settings)),

                # Docstring region.
                Window(height=D.exact(1),
                       content=FillControl('\u2500', token=Token.Separator),
                       filter=_HasSignature(settings) & _ShowDocstring(settings) & ~IsDone()),
                Window(
                    BufferControl(
                        buffer_name='docstring',
                        default_token=Token.Docstring,
                        #lexer=PythonLexer,
                    ),
                    filter=_HasSignature(settings) & _ShowDocstring(settings) & ~IsDone(),
                    height=D(max=12),
                ),
            ]),
            ] + extra_sidebars + [
            PythonSidebar(settings, key_bindings_manager),
        ]),
        VSplit([
            PythonToolbar(key_bindings_manager, settings),
            ShowSidebarButtonInfo(),
        ])
    ])


class PythonCommandLineInterface(object):
    def __init__(self,
                 get_globals=None, get_locals=None,
                 stdin=None, stdout=None,
                 vi_mode=False, history_filename=None,
                 style=PythonStyle,

                 # For internal use.
                 _completer=None,
                 _validator=None,
                 _python_prompt_control=None,
                 _extra_buffers=None,
                 _extra_sidebars=None):

        self.settings = PythonCLISettings()

        self.get_globals = get_globals or (lambda: {})
        self.get_locals = get_locals or self.get_globals

        self.completer = _completer or PythonCompleter(self.get_globals, self.get_locals)
        self.validator = _validator or PythonValidator()
        self.history = FileHistory(history_filename) if history_filename else History()
        self.python_prompt_control = _python_prompt_control or PythonPrompt(self.settings)
        self._extra_sidebars = _extra_sidebars or []

        # Use a KeyBindingManager for loading the key bindings.
        self.key_bindings_manager = KeyBindingManager(enable_vi_mode=vi_mode, enable_system_prompt=True)
        load_python_bindings(self.key_bindings_manager, self.settings,
                             add_buffer=self.add_new_python_buffer,
                             close_current_buffer=self.close_current_python_buffer)

        self.get_signatures_thread_running = False

        buffers = {
            'default': Buffer(focussable=filters.AlwaysOff()),  # Never use or focus the default buffer.
            'docstring': Buffer(focussable=_HasSignature(self.settings) & _ShowDocstring(self.settings)),
                                # XXX: also make docstring read only.
        }
        buffers.update(_extra_buffers or {})

        self.cli = CommandLineInterface(
            style=style,
            key_bindings_registry=self.key_bindings_manager.registry,
            buffers=buffers,
            create_async_autocompleters=True)

        def on_input_timeout():
            """
            When there is no input activity,
            in another thread, get the signature of the current code.
            """
            if not self.cli.focus_stack.current.startswith('python-'):
                return

            # Never run multiple get-signature threads.
            if self.get_signatures_thread_running:
                return
            self.get_signatures_thread_running = True

            buffer = self.cli.current_buffer
            document = buffer.document

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
                if buffer.text == document.text:
                    buffer.signatures = signatures

                    # Set docstring in docstring buffer.
                    if signatures:
                        string = signatures[0].docstring()
                        if not isinstance(string, six.text_type):
                            string = string.decode('utf-8')
                        self.cli.buffers['docstring'].reset(
                            initial_document=Document(string, cursor_position=0))
                    else:
                        self.cli.buffers['docstring'].reset()

                    self.cli.request_redraw()
                else:
                    on_input_timeout()

            self.cli.run_in_executor(run)

        self.cli.onInputTimeout += on_input_timeout
        self.cli.onReset += self.key_bindings_manager.reset

        self.add_new_python_buffer()

    def _update_layout(self):
        """
        Generate new layout.
        (To be done when we add/remove buffers.)
        """
        self.cli.layout = _create_layout(
            self.cli.buffers, self.settings, self.key_bindings_manager, self.python_prompt_control,
            extra_sidebars=self._extra_sidebars)

    def add_new_python_buffer(self):
        # Create a new buffer.
        buffer = self._create_buffer()
        self.settings.buffer_index += 1
        name = 'python-%i' % self.settings.buffer_index

        # Insert and update layout.
        self.cli.add_buffer(name, buffer, focus=True)
        self._update_layout()

    def close_current_python_buffer(self):
        name, _ = current_python_buffer(self.cli, self.settings)

        if name:
            python_buffers_left = len([b for b in self.cli.buffers if b.startswith('python-')])

            if python_buffers_left > 1:
                focus_next_buffer(self.cli, name_filter=lambda name: name.startswith('python-'))
                del self.cli.buffers[name]
                self._update_layout()
            else:
                self.cli.set_exit()

    def _create_buffer(self):
        def is_buffer_multiline(document):
            return (self.settings.paste_mode or
                    self.settings.currently_multiline or
                    document_is_multiline_python(document))

        return PythonBuffer(
            is_multiline=is_buffer_multiline,
            tempfile_suffix='.py',
            history=self.history,
            completer=self.completer,
            validator=self.validator)
