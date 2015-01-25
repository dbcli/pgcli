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
from prompt_toolkit.filters import Filter
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.key_binding.vi_state import ViState
from prompt_toolkit.key_binding.bindings.emacs import load_emacs_bindings, load_emacs_system_bindings, load_emacs_search_bindings, load_emacs_open_in_editor_bindings
from prompt_toolkit.key_binding.bindings.vi import load_vi_bindings, load_vi_system_bindings, load_vi_search_bindings, load_vi_open_in_editor_bindings

__all__ = (
    'KeyBindingManager',
)


class ManagerFilter(Filter):
    def __init__(self, manager):
        self.manager = manager


class ViModeEnabled(ManagerFilter):
    def __call__(self, cli):
        return self.manager.enable_vi_mode


class SystemPromptEnabled(ManagerFilter):
    def __call__(self, cli):
        return self.manager.enable_system_prompt


class SearchEnabled(ManagerFilter):
    def __call__(self, cli):
        return self.manager.enable_search


class OpenInEditorEnabled(ManagerFilter):
    def __call__(self, cli):
        return self.manager.enable_open_in_editor


class KeyBindingManager(object):
    def __init__(self, registry=None, enable_vi_mode=False,
                 enable_system_prompt=False, enable_search=True,
                 enable_open_in_editor=False):

        self.registry = registry or Registry()

        # Flags. You can change these anytime.
        self.enable_vi_mode = enable_vi_mode
        self.enable_system_prompt = enable_system_prompt
        self.enable_search = enable_search
        self.enable_open_in_editor = enable_open_in_editor

        # Create set of filters to enable/disable sets of key bindings at
        # runtime.
        vi_mode_enabled = ViModeEnabled(self)
        emacs_mode_enabled = ~ vi_mode_enabled
        system_prompt_enabled = SystemPromptEnabled(self)
        search_enabled = SearchEnabled(self)
        open_in_editor_enabled = OpenInEditorEnabled(self)

        # Vi state. (Object to keep track of in which Vi mode we are.)
        self.vi_state = ViState()

        # Load all bindings in the registry with the correct filters.
        load_emacs_bindings(self.registry, emacs_mode_enabled)
        load_emacs_open_in_editor_bindings(
            self.registry, emacs_mode_enabled & open_in_editor_enabled)
        load_emacs_search_bindings(
            self.registry, emacs_mode_enabled & search_enabled)
        load_emacs_system_bindings(
            self.registry, emacs_mode_enabled & system_prompt_enabled)

        load_vi_bindings(self.registry, self.vi_state, vi_mode_enabled)
        load_vi_open_in_editor_bindings(
            self.registry, self.vi_state,
            vi_mode_enabled & open_in_editor_enabled)
        load_vi_search_bindings(
            self.registry, self.vi_state,
            vi_mode_enabled & search_enabled)
        load_vi_system_bindings(
            self.registry, self.vi_state,
            vi_mode_enabled & system_prompt_enabled)

    def reset(self):
        self.vi_state.reset()
