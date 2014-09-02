"""
Useful shortcuts.
"""
from __future__ import unicode_literals

from .. import CommandLine, AbortAction
from ..prompt import Prompt, PasswordProcessor
from ..inputstream_handler import EmacsInputStreamHandler
from ..line import Line


def get_input(message, raise_exception_on_abort=False, multiline=False, is_password=False):
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


    class CLI(CommandLine):
        prompt_factory = CustomPrompt
        inputstream_handler_factory = EmacsInputStreamHandler
        line_factory = CustomLine


    cli = CLI()

    on_abort = AbortAction.RAISE_EXCEPTION if raise_exception_on_abort else AbortAction.RETURN_NONE
    code_obj = cli.read_input(on_abort=on_abort, on_exit=AbortAction.IGNORE)

    if code_obj:
        return code_obj.text
