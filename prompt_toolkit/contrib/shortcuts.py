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

from prompt_toolkit import CommandLineInterface, AbortAction
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.layout import Window, HSplit, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.layout.processors import PasswordProcessor
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.toolbars import ValidationToolbar, SystemToolbar
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.history import History, FileHistory


__all__ = (
    'get_input',
    'create_cli',
    'create_default_layout',
)


def create_default_layout(message='', lexer=None, is_password=False, reserve_space_for_menu=False):
    """
    Generate default layout.
    """
    # Create processors list.
    if is_password:
        input_processors = [PasswordProcessor(), DefaultPrompt(message)]
    else:
        input_processors = [DefaultPrompt(message)]

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
                      layout=CompletionsMenu(max_height=16))
            ]
        ),
        ValidationToolbar(),
        SystemToolbar(),
    ])


def create_cli(message='',
               multiline=False,
               is_password=False,
               vi_mode=False,
               lexer=None,
               enable_system_prompt=False,
               validator=None,
               completer=None,
               style=None,
               history_filename=None):

    # Create history instance.
    if history_filename:
        history = FileHistory(history_filename)
    else:
        history = History()

    # Load all key bindings.
    manager = KeyBindingManager(enable_vi_mode=vi_mode, enable_system_prompt=enable_system_prompt)

    # Create interface.
    return CommandLineInterface(
        layout=create_default_layout(message=message, lexer=lexer, is_password=is_password,
                                     reserve_space_for_menu=(completer is not None)),
        buffer=Buffer(
            is_multiline=multiline,
            history=history,
            validator=validator,
            completer=completer,
        ),
        key_bindings_registry=manager.registry,
        style=style)


def get_input(message='',
              raise_exception_on_abort=False,
              multiline=False,
              is_password=False,
              vi_mode=False,
              lexer=None,
              validator=None,
              completer=None,
              style=None,
              enable_system_prompt=False,
              history_filename=None):
    """
    Get input from the user and return it. This wrapper builds the most obvious
    configuration of a `CommandLineInterface`. This can be a replacement for
    `raw_input`. (or GNU readline.)

    This returns `None` when Ctrl-D was pressed.

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
    :param history_filename: If not `None`, keep a persistent history in this file.
    """
    cli = create_cli(
        message=message,
        multiline=multiline,
        is_password=is_password,
        vi_mode=vi_mode,
        lexer=lexer,
        enable_system_prompt=enable_system_prompt,
        validator=validator,
        completer=completer,
        style=style,
        history_filename=history_filename)

    # Read input and return it.
    on_abort = AbortAction.RAISE_EXCEPTION if raise_exception_on_abort else AbortAction.RETURN_NONE
    document = cli.read_input(on_abort=on_abort, on_exit=AbortAction.IGNORE)

    if document:
        return document.text
