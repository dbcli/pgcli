"""
:class:`KeyBindingManager` is a utility (or shortcut) for loading all the key
bindings in a key binding registry, with a logic set of filters to quickly to
quickly change from Vi to Emacs key bindings at runtime.

You don't have to use this, but it's practical.

Usage::

    manager = KeyBindingManager()
    cli = CommandLineInterface(key_bindings_registry=manager.registry)
"""
from __future__ import unicode_literals
from prompt_toolkit.key_binding.registry import Registry
from prompt_toolkit.key_binding.bindings.basic import load_basic_bindings, load_abort_and_exit_bindings, load_basic_system_bindings, load_auto_suggestion_bindings, load_mouse_bindings
from prompt_toolkit.key_binding.bindings.emacs import load_emacs_bindings, load_emacs_system_bindings, load_emacs_search_bindings, load_emacs_open_in_editor_bindings, load_extra_emacs_page_navigation_bindings
from prompt_toolkit.key_binding.bindings.vi import load_vi_bindings, load_vi_system_bindings, load_vi_search_bindings, load_vi_open_in_editor_bindings, load_extra_vi_page_navigation_bindings
from prompt_toolkit.filters import to_cli_filter

__all__ = (
    'KeyBindingManager',
)


class KeyBindingManager(object):
    """
    Utility for loading all key bindings into memory.

    :param registry: Optional `Registry` instance.
    :param enable_abort_and_exit_bindings: Filter to enable Ctrl-C and Ctrl-D.
    :param enable_system_bindings: Filter to enable the system bindings
            (meta-! prompt and Control-Z suspension.)
    :param enable_search: Filter to enable the search bindings.
    :param enable_open_in_editor: Filter to enable open-in-editor.
    :param enable_open_in_editor: Filter to enable open-in-editor.
    :param enable_extra_page_navigation: Filter for enabling extra page navigation.
        (Bindings for up/down scrolling through long pages, like in Emacs or Vi.)
    :param enable_auto_suggest_bindings: Filter to enable fish-style suggestions.
    :param enable_all: Filter to enable (or disable) all bindings.

    :param enable_vi_mode: Deprecated!
    """
    def __init__(self, registry=None,
                 enable_vi_mode=None,  # (`enable_vi_mode` is deprecated.)
                 get_search_state=None,
                 enable_abort_and_exit_bindings=False,
                 enable_system_bindings=False, enable_search=False,
                 enable_open_in_editor=False, enable_extra_page_navigation=False,
                 enable_auto_suggest_bindings=False,
                 enable_all=True):

        assert registry is None or isinstance(registry, Registry)
        assert get_search_state is None or callable(get_search_state)

        # Create registry.
        self.registry = registry or Registry()

        # Accept both Filters and booleans as input.
        enable_abort_and_exit_bindings = to_cli_filter(enable_abort_and_exit_bindings)
        enable_system_bindings = to_cli_filter(enable_system_bindings)
        enable_search = to_cli_filter(enable_search)
        enable_open_in_editor = to_cli_filter(enable_open_in_editor)
        enable_extra_page_navigation = to_cli_filter(enable_extra_page_navigation)
        enable_auto_suggest_bindings = to_cli_filter(enable_auto_suggest_bindings)
        enable_all = to_cli_filter(enable_all)

        # Load basic bindings.
        load_basic_bindings(self.registry, enable_all)
        load_mouse_bindings(self.registry, enable_all)

        load_abort_and_exit_bindings(
            self.registry, enable_abort_and_exit_bindings & enable_all)

        load_basic_system_bindings(self.registry,
            enable_system_bindings & enable_all)

        # Load emacs bindings.
        load_emacs_bindings(self.registry, enable_all)

        load_emacs_open_in_editor_bindings(
            self.registry, enable_open_in_editor & enable_all)

        load_emacs_search_bindings(
            self.registry,
            filter=enable_search & enable_all,
            get_search_state=get_search_state)

        load_emacs_system_bindings(
            self.registry, enable_system_bindings & enable_all)

        load_extra_emacs_page_navigation_bindings(
            self.registry,
            enable_extra_page_navigation & enable_all)

        # Load Vi bindings.
        load_vi_bindings(
            self.registry, enable_visual_key=~enable_open_in_editor,
            filter=enable_all,
            get_search_state=get_search_state)

        load_vi_open_in_editor_bindings(
            self.registry,
            enable_open_in_editor & enable_all)

        load_vi_search_bindings(
            self.registry,
            filter=enable_search & enable_all,
            get_search_state=get_search_state)

        load_vi_system_bindings(
            self.registry,
            enable_system_bindings & enable_all)

        load_extra_vi_page_navigation_bindings(
            self.registry,
            enable_extra_page_navigation & enable_all)

        # Suggestion bindings.
        # (This has to come at the end, because the Vi bindings also have an
        # implementation for the "right arrow", but we really want the
        # suggestion binding when a suggestion is available.)
        load_auto_suggestion_bindings(
            self.registry,
            enable_auto_suggest_bindings & enable_all)

    @classmethod
    def for_prompt(cls, **kw):
        """
        Create a ``KeyBindingManager`` with the defaults for an input prompt.
        This activates the key bindings for abort/exit (Ctrl-C/Ctrl-D),
        incremental search and auto suggestions.

        (Not for full screen applications.)
        """
        kw.setdefault('enable_abort_and_exit_bindings', True)
        kw.setdefault('enable_search', True)
        kw.setdefault('enable_auto_suggest_bindings', True)

        return cls(**kw)

    def reset(self, cli):
        # For backwards compatibility.
        pass

    def get_vi_state(self, cli):
        # Deprecated!
        return cli.vi_state
