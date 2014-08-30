"""
Useful shortcuts.
"""
from __future__ import unicode_literals

from .. import CommandLine, AbortAction
from ..prompt import Prompt
from ..inputstream_handler import EmacsInputStreamHandler
from ..line import Line


def get_input(message, raise_exception_on_abort=False, multiline=False):
    """
    Replacement for `raw_input`.
    Ask for input, return the answer.
    This returns `None` when Ctrl-D was pressed.
    """
    class CustomPrompt(Prompt):
        default_prompt_text = message


    class CustomLine(Line):
        is_multiline = multiline


    class CLI(CommandLine):
        prompt_cls = CustomPrompt
        inputstream_handler_cls = EmacsInputStreamHandler
        line_cls = CustomLine


    cli = CLI()

    on_abort = AbortAction.RAISE_EXCEPTION if raise_exception_on_abort else AbortAction.RETURN_NONE
    code_obj = cli.read_input(on_abort=on_abort, on_exit=AbortAction.IGNORE)

    if code_obj:
        return code_obj.text
