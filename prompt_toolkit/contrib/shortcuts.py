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

from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import IsDone, HasFocus
from prompt_toolkit.history import History
from prompt_toolkit.interface import CommandLineInterface, AbortAction, AcceptAction
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.layout import Window, HSplit, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl, TokenListControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import PasswordProcessor, HighlightSearchProcessor, HighlightSelectionProcessor
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.screen import Char
from prompt_toolkit.layout.toolbars import ValidationToolbar, SystemToolbar

from pygments.token import Token


__all__ = (
    'get_input',
    'create_cli',
    'create_default_layout',
)


def create_default_layout(message='', lexer=None, is_password=False,
                          reserve_space_for_menu=False, get_bottom_toolbar_tokens=None):
    """
    Generate default layout.
    """
    assert get_bottom_toolbar_tokens is None or callable(get_bottom_toolbar_tokens)

    # Create processors list.
    input_processors = [HighlightSearchProcessor(), HighlightSelectionProcessor()]
    if is_password:
        input_processors.extend([PasswordProcessor(), DefaultPrompt(message)])
    else:
        input_processors.append(DefaultPrompt(message))

    # Create bottom toolbar.
    if get_bottom_toolbar_tokens:
        toolbars = [Window(TokenListControl(get_bottom_toolbar_tokens,
                                            default_char=Char(' ', Token.Toolbar)),
                           height=LayoutDimension.exact(1),
                           filter=~IsDone())]
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
                    lexer=lexer),
                get_height=get_height,
            ),
            [
                Float(xcursor=True,
                      ycursor=True,
                      content=CompletionsMenu(max_height=16,
                                              extra_filter=HasFocus('default')))
            ]
        ),
        ValidationToolbar(),
        SystemToolbar(),
    ] + toolbars)


def create_cli(message='',
               multiline=False,
               is_password=False,
               vi_mode=False,
               lexer=None,
               enable_system_prompt=False,
               enable_open_in_editor=False,
               validator=None,
               completer=None,
               style=None,
               history=None,
               get_bottom_toolbar_tokens=None,
               key_bindings_registry=None,
               output=None,
               on_abort=AbortAction.RAISE_EXCEPTION,
               on_exit=AbortAction.RAISE_EXCEPTION,
               on_accept=AcceptAction.RETURN_DOCUMENT):
    """
    Create a `CommandLineInterface` instance.
    """
    # Create history instance.
    if history is None:
        history = History()

    # Use default registry from KeyBindingManager if none was given.
    if key_bindings_registry is None:
        key_bindings_registry = KeyBindingManager(
            enable_vi_mode=vi_mode,
            enable_system_prompt=enable_system_prompt,
            enable_open_in_editor=enable_open_in_editor).registry

    # Create interface.
    return CommandLineInterface(
        layout=create_default_layout(message=message, lexer=lexer, is_password=is_password,
                                     reserve_space_for_menu=(completer is not None),
                                     get_bottom_toolbar_tokens=get_bottom_toolbar_tokens),
        buffer=Buffer(
            is_multiline=multiline,
            history=history,
            validator=validator,
            completer=completer,
        ),
        key_bindings_registry=key_bindings_registry,
        style=style,
        output=output,
        on_abort=on_abort,
        on_exit=on_exit)


def get_input(message='',
              on_abort=AbortAction.RAISE_EXCEPTION,
              on_exit=AbortAction.RAISE_EXCEPTION,
              on_accept=AcceptAction.RETURN_DOCUMENT,
              multiline=False,
              is_password=False,
              vi_mode=False,
              lexer=None,
              validator=None,
              completer=None,
              style=None,
              enable_system_prompt=False,
              enable_open_in_editor=False,
              history=None,
              get_bottom_toolbar_tokens=None,
              key_bindings_registry=None):
    """
    Get input from the user and return it. This wrapper builds the most obvious
    configuration of a `CommandLineInterface`. This can be a replacement for
    `raw_input`. (or GNU readline.)

    This returns `None` when Ctrl-D was pressed.

    If you want to keep your history across several ``get_input`` calls, you
    have to create a :class:`History` instance and pass it every time.

    :param message: Text to be shown before the prompt.
    :param mulitiline: Allow multiline input. Pressing enter will insert a
                       newline. (This requires Meta+Enter to accept the input.)
    :param is_password: Show asterisks instead of the actual typed characters.
    :param vi_mode: If True, use Vi key bindings.
    :param lexer: Pygments lexer to be used for the syntax highlighting.
    :param validator: `Validator` instance for input validation.
    :param completer: `Completer` instance for input completion.
    :param style: Pygments style class for the color scheme.
    :param enable_system_prompt: Pressing Meta+'!' will show a system prompt.
    :param enable_open_in_editor: Pressing 'v' in Vi mode or C-X C-E in emacs
                                  mode will open an external editor.
    :param history: `History` instance. (e.g. `FileHistory`)
    :param get_bottom_toolbar_tokens: Optional callable which takes a
        :class:`CommandLineInterface` and returns a list of tokens for the
        bottom toolbar.
    """
    cli = create_cli(
        message=message,
        multiline=multiline,
        is_password=is_password,
        vi_mode=vi_mode,
        lexer=lexer,
        enable_system_prompt=enable_system_prompt,
        enable_open_in_editor=enable_open_in_editor,
        validator=validator,
        completer=completer,
        style=style,
        history=history,
        get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
        key_bindings_registry=key_bindings_registry,
        on_abort=on_abort,
        on_exit=on_exit,
        on_accept=on_accept)

    # Read input and return it.
    document = cli.read_input()

    if document:
        return document.text
