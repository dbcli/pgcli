"""
:class:`KeyBindingManager` is a utility (or shortcut) for loading all the key
bindings in a key binding registry, with a logic set of filters to quickly to
quickly change from Vi to Emacs key bindings at runtime.

You don't have to use this, but it's practical.

Usage::

    manager = KeyBindingManager()
    cli = CommandLineInterface(key_bindings_registry=manager.registry)
    manager.enable_vi_mode = True
"""
from __future__ import unicode_literals
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.key_binding.vi_state import ViState
from prompt_toolkit.key_binding.bindings.emacs import load_emacs_bindings, load_emacs_system_bindings, load_emacs_search_bindings, load_emacs_open_in_editor_bindings
from prompt_toolkit.key_binding.bindings.vi import load_vi_bindings, load_vi_system_bindings, load_vi_search_bindings, load_vi_open_in_editor_bindings
from prompt_toolkit.filters import CLIFilter, Never, Always

__all__ = (
    'KeyBindingManager',
)


class KeyBindingManager(object):
    def __init__(self, registry=None, enable_vi_mode=Never(),
                 enable_system_prompt=Never(), enable_search=Always(),
                 enable_open_in_editor=Never()):

        assert registry is None or isinstance(registry, Registry)
        assert isinstance(enable_vi_mode, CLIFilter)
        assert isinstance(enable_system_prompt, CLIFilter)
        assert isinstance(enable_open_in_editor, CLIFilter)

        self.registry = registry or Registry()

        # Emacs mode filter is the opposite of Vi mode.
        enable_emacs_mode = ~enable_vi_mode

        # Vi state. (Object to keep track of in which Vi mode we are.)
        self.vi_state = ViState()

        # Load emacs bindings.
        load_emacs_bindings(self.registry, enable_emacs_mode)

        load_emacs_open_in_editor_bindings(
            self.registry, enable_emacs_mode & enable_open_in_editor)

        load_emacs_search_bindings(
            self.registry, enable_emacs_mode & enable_search)

        load_emacs_system_bindings(
            self.registry, enable_emacs_mode & enable_system_prompt)

        # Load Vi bindings.
        load_vi_bindings(self.registry, self.vi_state, enable_vi_mode)

        load_vi_open_in_editor_bindings(
            self.registry, self.vi_state,
            enable_vi_mode & enable_open_in_editor)

        load_vi_search_bindings(
            self.registry, self.vi_state,
            enable_vi_mode & enable_search)

        load_vi_system_bindings(
            self.registry, self.vi_state,
            enable_vi_mode & enable_system_prompt)

    def reset(self):
        self.vi_state.reset()
