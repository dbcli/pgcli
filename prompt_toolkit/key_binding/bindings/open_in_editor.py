"""
Open in editor key bindings.
"""
from __future__ import unicode_literals
from ..key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.filters import emacs_mode, vi_navigation_mode, has_selection
from .named_commands import get_by_name

__all__ = [
    'load_open_in_editor_bindings',
    'load_emacs_open_in_editor_bindings',
    'load_vi_open_in_editor_bindings',
]


def load_open_in_editor_bindings():
    """
    Load both the Vi and emacs key bindings for handling edit-and-execute-command.
    """
    return merge_key_bindings([
        load_emacs_open_in_editor_bindings(),
        load_vi_open_in_editor_bindings(),
    ])


def load_emacs_open_in_editor_bindings():
    """
    Pressing C-X C-E will open the buffer in an external editor.
    """
    key_bindings = KeyBindings()

    key_bindings.add('c-x', 'c-e',
                     filter=emacs_mode & ~has_selection)(
        get_by_name('edit-and-execute-command'))

    return key_bindings


def load_vi_open_in_editor_bindings():
    """
    Pressing 'v' in navigation mode will open the buffer in an external editor.
    """
    key_bindings = KeyBindings()
    key_bindings.add('v', filter=vi_navigation_mode)(
        get_by_name('edit-and-execute-command'))
    return key_bindings
