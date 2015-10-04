"""
Useful shortcuts for creating a `CommandLineInterface` and reading input from it.
------------------------------------------------------------------------ --------

If you are using this library for retrieving some input from the user (as a
pure Python replacement for GNU readline), probably for 90% of the use cases,
the `prompt` function is all you need. It's the easiest shortcut which does
a lot of the underlying work like creating a `CommandLineInterface` instance
for you.

When is this not sufficient:
    - When you want to have more complicated layouts (maybe with sidebars or
      multiple toolbars. Or visibility of certain user interface controls
      according to some conditions.)
    - When you wish to have multiple input buffers. (If you would create an
      editor like a Vi clone.)
    - Something else that requires more customization than what is possible
      with the parameters of `prompt`.

In that case, study the code in this file and build your own
`CommandLineInterface` instance. It's not too complicated.
"""
from __future__ import unicode_literals

from .buffer import Buffer
from .document import Document
from .enums import DEFAULT_BUFFER, SEARCH_BUFFER
from .filters import IsDone, HasFocus, RendererHeightIsKnown, to_simple_filter, to_cli_filter, Condition
from .history import InMemoryHistory
from .interface import CommandLineInterface, Application, AbortAction, AcceptAction
from .key_binding.manager import KeyBindingManager
from .layout import Window, HSplit, VSplit, FloatContainer, Float
from .layout.containers import ConditionalContainer
from .layout.controls import BufferControl, TokenListControl
from .layout.dimension import LayoutDimension
from .layout.lexers import PygmentsLexer
from .layout.menus import CompletionsMenu, MultiColumnCompletionsMenu
from .layout.processors import PasswordProcessor, HighlightSearchProcessor, HighlightSelectionProcessor, ConditionalProcessor, AppendAutoSuggestion
from .layout.prompt import DefaultPrompt
from .layout.screen import Char
from .layout.toolbars import ValidationToolbar, SystemToolbar, ArgToolbar, SearchToolbar
from .layout.utils import explode_tokens
from .styles import DefaultStyle
from .utils import is_conemu_ansi, is_windows

from pygments.token import Token
from six import text_type

import pygments.lexer
import sys

if is_windows():
    from .terminal.win32_output import Win32Output
    from .terminal.conemu_output import ConEmuOutput
else:
    from .terminal.vt100_output import Vt100_Output


__all__ = (
    'create_eventloop',
    'create_default_output',
    'create_default_layout',
    'create_default_application',
    'prompt',
)


def create_eventloop(inputhook=None):
    """
    Create and return a normal `EventLoop` instance for a
    `CommandLineInterface`.
    """
    if is_windows():
        from prompt_toolkit.eventloop.win32 import Win32EventLoop as Loop
    else:
        from prompt_toolkit.eventloop.posix import PosixEventLoop as Loop

    return Loop(inputhook=inputhook)


def create_default_output(stdout=None):
    """
    Return an `Output` instance for the command line.
    """
    stdout = stdout or sys.__stdout__

    if is_windows():
        if is_conemu_ansi():
            return ConEmuOutput(stdout)
        else:
            return Win32Output(stdout)
    else:
        return Vt100_Output.from_pty(stdout)


def create_asyncio_eventloop(loop=None):
    """
    Returns an asyncio `Eventloop` instance for usage in a
    `CommandLineInterface`. It is a wrapper around an asyncio loop.

    :param loop: The asyncio eventloop (or `None` if the default asyncioloop
                 should be used.)
    """
    # Inline import, to make sure the rest doesn't break on Python 2. (Where
    # asyncio is not available.)
    if is_windows():
        from prompt_toolkit.eventloop.asyncio_win32 import Win32AsyncioEventLoop as AsyncioEventLoop
    else:
        from prompt_toolkit.eventloop.asyncio_posix import PosixAsyncioEventLoop as AsyncioEventLoop

    return AsyncioEventLoop(loop)


def _split_multiline_prompt(get_prompt_tokens):
    """
    Take a `get_prompt_tokens` function. and return two new functions instead.
    One that returns the tokens to be shown on the lines above the input, and
    another one with the tokens to be shown at the first line of the input.
    """
    def before(cli):
        result = []
        found_nl = False
        for token, char in reversed(explode_tokens(get_prompt_tokens(cli))):
            if char == '\n':
                found_nl = True
            elif found_nl:
                result.insert(0, (token, char))
        return result

    def first_input_line(cli):
        result = []
        for token, char in reversed(explode_tokens(get_prompt_tokens(cli))):
            if char == '\n':
                break
            else:
                result.insert(0, (token, char))
        return result

    return before, first_input_line


def create_default_layout(message='', lexer=None, is_password=False,
                          reserve_space_for_menu=False,
                          get_prompt_tokens=None, get_bottom_toolbar_tokens=None,
                          display_completions_in_columns=False,
                          extra_input_processors=None, multiline=False,
                          wrap_lines=True):
    """
    Generate default layout.
    Returns a ``Layout`` instance.

    :param message: Text to be used as prompt.
    :param lexer: Lexer to be used for the highlighting.
    :param is_password: `bool` or `CLIFilter`. When True, display input as '*'.
    :param reserve_space_for_menu: When True, make sure that a minimal height is
        allocated in the terminal, in order to display the completion menu.
    :param get_prompt_tokens: An optional callable that returns the tokens to be
        shown in the menu. (To be used instead of a `message`.)
    :param get_bottom_toolbar_tokens: An optional callable that returns the
        tokens for a toolbar at the bottom.
    :param display_completions_in_columns: `bool` or `CLIFilter`. Display the
        completions in multiple columns.
    :param multiline: `bool` or `CLIFilter`. When True, prefer a layout that is
        more adapted for multiline input. Text after newlines is automatically
        indented, and search/arg input is shown below the input, instead of
        replacing the prompt.
    :param wrap_lines: `bool` or `CLIFilter`. When True (the default),
        automatically wrap long lines instead of scrolling horizontally.
    """
    assert isinstance(message, text_type)
    assert get_bottom_toolbar_tokens is None or callable(get_bottom_toolbar_tokens)
    assert get_prompt_tokens is None or callable(get_prompt_tokens)
    assert not (message and get_prompt_tokens)

    display_completions_in_columns = to_cli_filter(display_completions_in_columns)
    multiline = to_cli_filter(multiline)

    if get_prompt_tokens is None:
        get_prompt_tokens = lambda _: [(Token.Prompt, message)]

    get_prompt_tokens_1, get_prompt_tokens_2 = _split_multiline_prompt(get_prompt_tokens)

    # `lexer` is supposed to be a `Lexer` instance. But if a Pygments lexer
    # class is given, turn it into a PygmentsLexer. (Important for
    # backwards-compatibility.)
    try:
        if issubclass(lexer, pygments.lexer.Lexer):
            lexer = PygmentsLexer(lexer)
    except TypeError: # Happens when lexer is `None` or an instance of something else.
        pass

    # Create processors list.
    # (DefaultPrompt should always be at the end.)
    input_processors = [ConditionalProcessor(
                            # By default, only highlight search when the search
                            # input has the focus. (Note that this doesn't mean
                            # there is no search: the Vi 'n' binding for instance
                            # still allows to jump to the next match in
                            # navigation mode.)
                            HighlightSearchProcessor(preview_search=True),
                            HasFocus(SEARCH_BUFFER)),
                        HighlightSelectionProcessor(),
                        ConditionalProcessor(AppendAutoSuggestion(), HasFocus(DEFAULT_BUFFER) & ~IsDone()),
                        ConditionalProcessor(PasswordProcessor(), is_password)]

    if extra_input_processors:
        input_processors.extend(extra_input_processors)

    # Show the prompt before the input (using the DefaultPrompt processor.
    # This also replaces it with reverse-i-search and 'arg' when required.
    # (Only for single line mode.)
    input_processors.append(ConditionalProcessor(
        DefaultPrompt(get_prompt_tokens), ~multiline))

    # Create bottom toolbar.
    if get_bottom_toolbar_tokens:
        toolbars = [ConditionalContainer(
            Window(TokenListControl(get_bottom_toolbar_tokens,
                                    default_char=Char(' ', Token.Toolbar)),
                                    height=LayoutDimension.exact(1)),
            filter=~IsDone() & RendererHeightIsKnown())]
    else:
        toolbars = []

    def get_height(cli):
        # If there is an autocompletion menu to be shown, make sure that our
        # layout has at least a minimal height in order to display it.
        if reserve_space_for_menu and not cli.is_done:
            return LayoutDimension(min=8)
        else:
            return LayoutDimension()

    # Create and return Layout instance.
    return HSplit([
        ConditionalContainer(
            Window(
                TokenListControl(get_prompt_tokens_1),
                dont_extend_height=True),
            filter=multiline,
        ),
        VSplit([
            # In multiline mode, the prompt is displayed in a left pane.
            ConditionalContainer(
                Window(
                    TokenListControl(get_prompt_tokens_2),
                    dont_extend_width=True,
                ),
                filter=multiline,
            ),
            # The main input, with completion menus floating on top of it.
            FloatContainer(
                Window(
                    BufferControl(
                        input_processors=input_processors,
                        lexer=lexer,
                        wrap_lines=wrap_lines,
                        # Enable preview_search, we want to have immediate feedback
                        # in reverse-i-search mode.
                        preview_search=True),
                    get_height=get_height,
                ),
                [
                    Float(xcursor=True,
                          ycursor=True,
                          content=CompletionsMenu(
                              max_height=16,
                              scroll_offset=1,
                              extra_filter=HasFocus(DEFAULT_BUFFER) &
                                           ~display_completions_in_columns)),
                    Float(xcursor=True,
                          ycursor=True,
                          content=MultiColumnCompletionsMenu(
                              extra_filter=HasFocus(DEFAULT_BUFFER) &
                                           display_completions_in_columns,
                              show_meta=True))
                ]
            ),
        ]),
        ValidationToolbar(),
        SystemToolbar(),

        # In multiline mode, we use two toolbars for 'arg' and 'search'.
        ConditionalContainer(ArgToolbar(), multiline),
        ConditionalContainer(SearchToolbar(), multiline),
    ] + toolbars)


def create_default_application(
        message='',
        multiline=False,
        wrap_lines=True,
        is_password=False,
        vi_mode=False,
        complete_while_typing=True,
        enable_history_search=False,
        lexer=None,
        enable_system_bindings=False,
        enable_open_in_editor=False,
        validator=None,
        completer=None,
        auto_suggest=None,
        style=None,
        history=None,
        clipboard=None,
        get_prompt_tokens=None,
        get_bottom_toolbar_tokens=None,
        display_completions_in_columns=False,
        get_title=None,
        mouse_support=False,
        extra_input_processors=None,
        key_bindings_registry=None,
        on_abort=AbortAction.RAISE_EXCEPTION,
        on_exit=AbortAction.RAISE_EXCEPTION,
        accept_action=AcceptAction.RETURN_DOCUMENT,
        default=''):
    """
    Create a default `Aplication` instance.
    It is meant to cover 90% of the use cases, where no extreme customization
    is required.

    :param message: Text to be shown before the prompt.
    :param mulitiline: Allow multiline input. Pressing enter will insert a
                       newline. (This requires Meta+Enter to accept the input.)
    :param wrap_lines: `bool` or `CLIFilter`. When True (the default),
        automatically wrap long lines instead of scrolling horizontally.
    :param is_password: Show asterisks instead of the actual typed characters.
    :param vi_mode: `bool` or `CLIFilter`. If True, use Vi key bindings.
    :param complete_while_typing: `bool` or `CLIFilter`. Enable autocompletion
        while typing.
    :param enable_history_search: `bool` or `CLIFilter`. Enable up-arrow
        parting string matching.
    :param lexer: Lexer to be used for the syntax highlighting.
    :param validator: `Validator` instance for input validation.
    :param completer: `Completer` instance for input completion.
    :param auto_suggest: `AutoSuggest` instance for input suggestions.
    :param style: Pygments style class for the color scheme.
    :param enable_system_bindings: `bool` or `CLIFilter`. Pressing Meta+'!'
        will show a system prompt.
    :param enable_open_in_editor: `bool` or `CLIFilter`. Pressing 'v' in Vi
        mode or C-X C-E in emacs mode will open an external editor.
    :param history: `History` instance. (e.g. `FileHistory`)
    :param clipboard: `Clipboard` instance. (e.g. `InMemoryClipboard`)
    :param get_bottom_toolbar_tokens: Optional callable which takes a
        :class:`CommandLineInterface` and returns a list of tokens for the
        bottom toolbar.
    :param display_completions_in_columns: `bool` or `CLIFilter`. Display the
        completions in multiple columns.
    :param get_title: Callable that returns the title to be displayed in the
        terminal.
    :param mouse_support: `bool` or `CLIFilter` to enable mouse support.
    :param default: The default text to be shown in the input buffer. (This can
        be edited by the user.)
    """
    if key_bindings_registry is None:
        key_bindings_registry = KeyBindingManager.for_prompt(
            enable_vi_mode=vi_mode,
            enable_system_bindings=enable_system_bindings,
            enable_open_in_editor=enable_open_in_editor).registry

    # Make sure that complete_while_typing is disabled when enable_history_search
    # is enabled. (First convert to SimpleFilter, to avoid doing bitwise operations
    # on bool objects.)
    complete_while_typing = to_simple_filter(complete_while_typing)
    enable_history_search = to_simple_filter(enable_history_search)
    multiline = to_simple_filter(multiline)

    complete_while_typing = complete_while_typing & ~enable_history_search

    # Create application
    return Application(
        layout=create_default_layout(
                message=message,
                lexer=lexer,
                is_password=is_password,
                reserve_space_for_menu=(completer is not None),
                multiline=Condition(lambda cli: multiline()),
                get_prompt_tokens=get_prompt_tokens,
                get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                display_completions_in_columns=display_completions_in_columns,
                extra_input_processors=extra_input_processors,
                wrap_lines=wrap_lines),
        buffer=Buffer(
                enable_history_search=enable_history_search,
                complete_while_typing=complete_while_typing,
                is_multiline=multiline,
                history=(history or InMemoryHistory()),
                validator=validator,
                completer=completer,
                auto_suggest=auto_suggest,
                accept_action=accept_action,
                initial_document=Document(default),
            ),
        style=style or DefaultStyle,
        clipboard=clipboard,
        key_bindings_registry=key_bindings_registry,
        get_title=get_title,
        mouse_support=mouse_support,
        on_abort=on_abort,
        on_exit=on_exit)


def prompt(message='', **kwargs):
    """
    Get input from the user and return it. This wrapper builds the most obvious
    configuration of a `CommandLineInterface`. This can be a replacement for
    `raw_input`. (or GNU readline.)

    If you want to keep your history across several ``prompt`` calls, you
    have to create a :class:`History` instance and pass it every time.
    """
    eventloop = kwargs.pop('eventloop', None) or create_eventloop()
    patch_stdout = kwargs.pop('patch_stdout', False)

    # Create CommandLineInterface
    cli = CommandLineInterface(
        application=create_default_application(message, **kwargs),
        eventloop=eventloop,
        output=create_default_output())

    # Replace stdout.
    original_stdout = sys.stdout

    if patch_stdout:
        sys.stdout = cli.stdout_proxy()

    # Read input and return it.

    # Note: We pass `reset_current_buffer=False`, because that way it's easy to
    #       give DEFAULT_BUFFER a default value, without it getting erased. We
    #       don't have to reset anyway, because this is the first and only time
    #       that this CommandLineInterface will run.
    try:
        document = cli.run(reset_current_buffer=False)

        if document:
            return document.text
    finally:
        eventloop.close()
        sys.stdout = original_stdout


# Deprecated alias for `prompt`.
get_input = prompt
