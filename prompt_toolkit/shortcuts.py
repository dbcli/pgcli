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
from .filters import IsDone, HasFocus, Always, Never, RendererHeightIsKnown
from .history import History
from .interface import CommandLineInterface, Application, AbortAction, AcceptAction
from .key_binding.manager import KeyBindingManager
from .layout import Window, HSplit, FloatContainer, Float
from .layout.controls import BufferControl, TokenListControl
from .layout.dimension import LayoutDimension
from .layout.menus import CompletionsMenu
from .layout.processors import PasswordProcessor, HighlightSearchProcessor, HighlightSelectionProcessor
from .layout.prompt import DefaultPrompt
from .layout.screen import Char
from .layout.toolbars import ValidationToolbar, SystemToolbar
from .styles import DefaultStyle

from pygments.token import Token
from six import text_type

import sys

if sys.platform == 'win32':
    from .terminal.win32_output import Win32Output
else:
    from .terminal.vt100_output import Vt100_Output


__all__ = (
    'create_eventloop',
    'create_default_output',
    'create_default_layout',
    'create_default_application',
    'get_input',
)


def create_eventloop():
    """
    Create and return a normal `EventLoop` instance for a
    `CommandLineInterface`.
    """
    if sys.platform == 'win32':
        from prompt_toolkit.eventloop.win32 import Win32EventLoop as Loop
    else:
        from prompt_toolkit.eventloop.posix import PosixEventLoop as Loop

    return Loop()


def create_default_output(stdout=None):
    """
    Return an `Output` instance for the command line.
    """
    stdout = stdout or sys.__stdout__

    if sys.platform == 'win32':
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
    if sys.platform == 'win32':
        from prompt_toolkit.eventloop.asyncio_win32 import Win32AsyncioEventLoop as AsyncioEventLoop
    else:
        from prompt_toolkit.eventloop.asyncio_posix import PosixAsyncioEventLoop as AsyncioEventLoop

    return AsyncioEventLoop(loop)


def create_default_layout(message='', lexer=None, is_password=False,
                          reserve_space_for_menu=False,
                          get_prompt_tokens=None, get_bottom_toolbar_tokens=None,
                          extra_input_processors=None):
    """
    Generate default layout.
    Returns a ``Layout`` instance.

    :param message: Text to be used as prompt.
    :param lexer: Pygments lexer to be used for the highlighting.
    :param is_password: When True, display input as '*'.
    :param reserve_space_for_menu: When True, make sure that a minimal height is
        allocated in the terminal, in order to display the completion menu.
    :param get_prompt_tokens: An optional callable that returns the tokens to be
        shown in the menu. (To be used instead of a `message`.)
    :param get_bottom_toolbar_tokens: An optional callable that returns the
        tokens for a toolbar at the bottom.
    """
    assert isinstance(message, text_type)
    assert get_bottom_toolbar_tokens is None or callable(get_bottom_toolbar_tokens)
    assert get_prompt_tokens is None or callable(get_prompt_tokens)
    assert not (message and get_prompt_tokens)

    # Create processors list.
    # (DefaultPrompt should always be at the end.)
    input_processors = [HighlightSearchProcessor(preview_search=Always()),
                        HighlightSelectionProcessor()]

    if is_password:
        input_processors.append(PasswordProcessor())

    if extra_input_processors:
        input_processors.extend(extra_input_processors)

    if get_prompt_tokens is None:
        input_processors.append(DefaultPrompt.from_message(message))
    else:
        input_processors.append(DefaultPrompt(get_prompt_tokens))

    # Create bottom toolbar.
    if get_bottom_toolbar_tokens:
        toolbars = [Window(TokenListControl(get_bottom_toolbar_tokens,
                                            default_char=Char(' ', Token.Toolbar)),
                           height=LayoutDimension.exact(1),
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
                      content=CompletionsMenu(max_height=16,
                                              extra_filter=HasFocus(DEFAULT_BUFFER)))
            ]
        ),
        ValidationToolbar(),
        SystemToolbar(),
    ] + toolbars)


def create_default_application(
        message='',
        multiline=False,
        is_password=False,
        vi_mode=Never(),
        lexer=None,
        enable_system_bindings=Never(),
        enable_open_in_editor=Never(),
        validator=None,
        completer=None,
        style=None,
        history=None,
        get_prompt_tokens=None,
        get_bottom_toolbar_tokens=None,
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
    :param lexer: Pygments lexer to be used for the syntax highlighting.
    :param validator: `Validator` instance for input validation.
    :param completer: `Completer` instance for input completion.
    :param style: Pygments style class for the color scheme.
    :param enable_system_bindings: Pressing Meta+'!' will show a system prompt.
    :param enable_open_in_editor: Pressing 'v' in Vi mode or C-X C-E in emacs
                                  mode will open an external editor.
    :param history: `History` instance. (e.g. `FileHistory`)
    :param get_bottom_toolbar_tokens: Optional callable which takes a
        :class:`CommandLineInterface` and returns a list of tokens for the
        bottom toolbar.
    """
    if key_bindings_registry is None:
        key_bindings_registry = KeyBindingManager(
            enable_vi_mode=vi_mode,
            enable_system_bindings=enable_system_bindings,
            enable_open_in_editor=enable_open_in_editor).registry

    return Application(
        layout=create_default_layout(
                message=message,
                lexer=lexer,
                is_password=is_password,
                reserve_space_for_menu=(completer is not None),
                get_prompt_tokens=get_prompt_tokens,
                get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                extra_input_processors=extra_input_processors),
        buffer=Buffer(
                is_multiline=(Always() if multiline else Never()),
                history=(history or History()),
                validator=validator,
                completer=completer,
                accept_action=accept_action,
            ),
        style=style or DefaultStyle,
        key_bindings_registry=key_bindings_registry,
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
    eventloop = create_eventloop()

    # Create CommandLineInterface
    cli = CommandLineInterface(
        application=create_default_application(message, **kwargs),
        eventloop=eventloop,
        output=create_default_output())

    # Read input and return it.
    try:
        document = cli.run()

        if document:
            return document.text
    finally:
        eventloop.close()
