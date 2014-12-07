"""
Useful shortcuts.
"""
from __future__ import unicode_literals

from prompt_toolkit import CommandLineInterface, AbortAction
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.key_binding.vi_state import ViState
from prompt_toolkit.key_binding.bindings.emacs import load_emacs_bindings, load_emacs_search_bindings
from prompt_toolkit.key_binding.bindings.vi import load_vi_bindings, load_vi_search_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.processors import PasswordProcessor
from prompt_toolkit.layout.prompt import DefaultPrompt


def get_input(message, raise_exception_on_abort=False, multiline=False, is_password=False, vi_mode=False):
    """
    Replacement for `raw_input`.
    Ask for input, return the answer.
    This returns `None` when Ctrl-D was pressed.
    """
    layout = Layout(
        before_input=DefaultPrompt(message),
        input_processors=([PasswordProcessor()] if is_password else []))

    registry = Registry()
    if vi_mode:
        vi_state = ViState()
        load_vi_bindings(registry, vi_state)
        load_vi_search_bindings(registry, vi_state)
    else:
        load_emacs_bindings(registry)
        load_emacs_search_bindings(registry)

    cli = CommandLineInterface(
        layout=layout,
        buffer=Buffer(is_multiline=multiline),
        key_bindings_registry=registry)

    on_abort = AbortAction.RAISE_EXCEPTION if raise_exception_on_abort else AbortAction.RETURN_NONE
    code = cli.read_input(on_abort=on_abort, on_exit=AbortAction.IGNORE)

    if code:
        return code.text
