"""
Useful shortcuts for creating a `CommandLineInterface` and reading input from it.
------------------------------------------------------------------------ --------

If you are using this library for retrieving some input from the user (as a
pure Python replacement for GNU readline), probably for 90% of the use cases,
the `get_input` function is all you need. It's the easiest shortcut which does
a lot of the underlying work like creating a `CommandLineInterface` instance
for you.

When is this not sufficient:
    - When you want to have more complicated layouts (maybe with sidebars or
      multiple toolbars. Or visibility of certain user interface controls
      according to some conditions.)
    - When you wish to have multiple input buffers. (If you would create an
      editor like a Vi clone.)
    - Something else that requires more customization than what is possible
      with the parameters of `get_input`.

In that case, study the code in this file and build your own
`CommandLineInterface` instance. It's not too complicated.
"""
from __future__ import unicode_literals

from .buffer import Buffer
from .enums import DEFAULT_BUFFER
from .filters import IsDone, HasFocus, Always, Never, RendererHeightIsKnown, to_simple_filter, to_cli_filter, Condition
from .history import History
from .interface import CommandLineInterface, Application, AbortAction, AcceptAction
from .key_binding.manager import KeyBindingManager
from .layout import Window, HSplit, VSplit, FloatContainer, Float
from .layout.containers import ConditionalContainer
from .layout.controls import BufferControl, TokenListControl
from .layout.dimension import LayoutDimension
from .layout.menus import CompletionsMenu, MultiColumnCompletionsMenu
from .layout.processors import PasswordProcessor, HighlightSearchProcessor, HighlightSelectionProcessor, ConditionalProcessor
from .layout.prompt import DefaultPrompt
from .layout.screen import Char
from .layout.toolbars import ValidationToolbar, SystemToolbar, ArgToolbar, SearchToolbar
from .styles import DefaultStyle
from .utils import is_conemu_ansi, is_windows

from pygments.token import Token
from six import text_type

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
    'get_input',
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


def create_default_layout(message='', lexer=None, is_password=False,
                          reserve_space_for_menu=False,
                          get_prompt_tokens=None, get_bottom_toolbar_tokens=None,
                          display_completions_in_columns=False,
                          extra_input_processors=None, multiline=False):
    """
    Generate default layout.
    Returns a ``Layout`` instance.

    :param message: Text to be used as prompt.
    :param lexer: Pygments lexer to be used for the highlighting.
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
    """
    assert isinstance(message, text_type)
    assert get_bottom_toolbar_tokens is None or callable(get_bottom_toolbar_tokens)
    assert get_prompt_tokens is None or callable(get_prompt_tokens)
    assert not (message and get_prompt_tokens)

    display_completions_in_columns = to_cli_filter(display_completions_in_columns)
    multiline = to_cli_filter(multiline)

    if get_prompt_tokens is None:
        get_prompt_tokens = lambda _: [(Token.Prompt, message)]

    # Create processors list.
    # (DefaultPrompt should always be at the end.)
    input_processors = [HighlightSearchProcessor(preview_search=Always()),
                        HighlightSelectionProcessor(),
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
        VSplit([
            # In multiline mode, the prompt is displayed in a left pane.
            ConditionalContainer(
                Window(
                    TokenListControl(get_prompt_tokens),
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
                        # Enable preview_search, we want to have immediate feedback
                        # in reverse-i-search mode.
                        preview_search=Always()),
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
                              show_meta=Always()))
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
        multiline=Never(),
        is_password=False,
        vi_mode=Never(),
        complete_while_typing=Always(),
        enable_history_search=Never(),
        lexer=None,
        enable_system_bindings=Never(),
        enable_open_in_editor=Never(),
        validator=None,
        completer=None,
        style=None,
        history=None,
        clipboard=None,
        get_prompt_tokens=None,
        get_bottom_toolbar_tokens=None,
        display_completions_in_columns=False,
        get_title=None,
        extra_input_processors=None,
        key_bindings_registry=None,
        on_abort=AbortAction.RAISE_EXCEPTION,
        on_exit=AbortAction.RAISE_EXCEPTION,
        accept_action=AcceptAction.RETURN_DOCUMENT):
    """
    Create a default `Aplication` instance.
    It is meant to cover 90% of the use cases, where no extreme customization
    is required.

    :param message: Text to be shown before the prompt.
    :param mulitiline: Allow multiline input. Pressing enter will insert a
                       newline. (This requires Meta+Enter to accept the input.)
    :param is_password: Show asterisks instead of the actual typed characters.
    :param vi_mode: If True, use Vi key bindings.
    :param complete_while_typing: Enable autocompletion while typing.
    :param enable_history_search: Enable up-arrow parting string matching.
    :param lexer: Pygments lexer to be used for the syntax highlighting.
    :param validator: `Validator` instance for input validation.
    :param completer: `Completer` instance for input completion.
    :param style: Pygments style class for the color scheme.
    :param enable_system_bindings: Pressing Meta+'!' will show a system prompt.
    :param enable_open_in_editor: Pressing 'v' in Vi mode or C-X C-E in emacs
                                  mode will open an external editor.
    :param history: `History` instance. (e.g. `FileHistory`)
    :param clipboard: `Clipboard` instance. (e.g. `InMemoryClipboard`)
    :param get_bottom_toolbar_tokens: Optional callable which takes a
        :class:`CommandLineInterface` and returns a list of tokens for the
        bottom toolbar.
    :param display_completions_in_columns: `bool` or `CLIFilter`. Display the
        completions in multiple columns.
    :param get_title: Callable that returns the title to be displayed in the
        terminal.
    """
    if key_bindings_registry is None:
        key_bindings_registry = KeyBindingManager(
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
                extra_input_processors=extra_input_processors),
        buffer=Buffer(
                enable_history_search=enable_history_search,
                complete_while_typing=complete_while_typing,
                is_multiline=multiline,
                history=(history or History()),
                validator=validator,
                completer=completer,
                accept_action=accept_action,
            ),
        style=style or DefaultStyle,
        clipboard=clipboard,
        key_bindings_registry=key_bindings_registry,
        get_title=get_title,
        on_abort=on_abort,
        on_exit=on_exit)


def get_input(message='', **kwargs):
    """
    Get input from the user and return it. This wrapper builds the most obvious
    configuration of a `CommandLineInterface`. This can be a replacement for
    `raw_input`. (or GNU readline.)

    If you want to keep your history across several ``get_input`` calls, you
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
    try:
        document = cli.run()

        if document:
            return document.text
    finally:
        eventloop.close()
        sys.stdout = original_stdout
