"""
Useful shortcuts.
"""
from __future__ import unicode_literals

from .. import CommandLineInterface, AbortAction
from ..key_bindings.emacs import emacs_bindings
from ..key_bindings.vi import vi_bindings
from ..line import Line
from ..prompt import Prompt, PasswordProcessor


def get_input(message, raise_exception_on_abort=False, multiline=False, is_password=False, vi_mode=False):
    """
    Replacement for `raw_input`.
    Ask for input, return the answer.
    This returns `None` when Ctrl-D was pressed.
    """
    class CustomPrompt(Prompt):
        prompt_text = message
        input_processors = ([PasswordProcessor()] if is_password else [])

    class CustomLine(Line):
        is_multiline = multiline


    class CLI(CommandLineInterface):
        prompt_factory = CustomPrompt
        line_factory = CustomLine
        key_bindings_factories = [ (vi_bindings if vi_mode else emacs_bindings) ]


    cli = CLI()

    on_abort = AbortAction.RAISE_EXCEPTION if raise_exception_on_abort else AbortAction.RETURN_NONE
    code_obj = cli.read_input(on_abort=on_abort, on_exit=AbortAction.IGNORE)

    if code_obj:
        return code_obj.text
