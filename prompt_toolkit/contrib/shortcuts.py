"""
Useful shortcuts.
"""
from __future__ import unicode_literals

from .. import CommandLineInterface, AbortAction
from ..key_bindings.emacs import emacs_bindings
from ..key_bindings.vi import vi_bindings
from ..line import Line
from ..layout import Layout
from ..layout.processors import PasswordProcessor
from ..layout.prompt import DefaultPrompt


def get_input(message, raise_exception_on_abort=False, multiline=False, is_password=False, vi_mode=False):
    """
    Replacement for `raw_input`.
    Ask for input, return the answer.
    This returns `None` when Ctrl-D was pressed.
    """
    layout = Layout(
        before_input=DefaultPrompt(message),
        input_processors=([PasswordProcessor()] if is_password else []))

    cli = CommandLineInterface(
        layout=layout,
        line=Line(is_multiline=multiline),
        key_binding_factories=[(vi_bindings if vi_mode else emacs_bindings)])

    on_abort = AbortAction.RAISE_EXCEPTION if raise_exception_on_abort else AbortAction.RETURN_NONE
    code = cli.read_input(on_abort=on_abort, on_exit=AbortAction.IGNORE)

    if code:
        return code.text
