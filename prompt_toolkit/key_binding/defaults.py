"""
Default key bindings.::

    key_bindings = load_key_bindings()
    app = Application(key_bindings=key_bindings)
"""
from __future__ import unicode_literals
from prompt_toolkit.key_binding.key_bindings import ConditionalKeyBindings, merge_key_bindings
from prompt_toolkit.key_binding.bindings.basic import load_basic_bindings, load_abort_and_exit_bindings, load_basic_system_bindings, load_auto_suggestion_bindings, load_mouse_bindings
from prompt_toolkit.key_binding.bindings.emacs import load_emacs_bindings, load_emacs_search_bindings, load_emacs_open_in_editor_bindings, load_extra_emacs_page_navigation_bindings
from prompt_toolkit.key_binding.bindings.vi import load_vi_bindings, load_vi_search_bindings, load_vi_open_in_editor_bindings, load_extra_vi_page_navigation_bindings
from prompt_toolkit.filters import to_filter

__all__ = (
    'load_key_bindings',
)


def load_key_bindings(
        enable_abort_and_exit_bindings=False,
        enable_system_bindings=False,
        enable_search=True,
        enable_open_in_editor=False,
        enable_extra_page_navigation=False,
        enable_auto_suggest_bindings=False):
    """
    Create a KeyBindings object that contains the default key bindings.

    :param enable_abort_and_exit_bindings: Filter to enable Ctrl-C and Ctrl-D.
    :param enable_system_bindings: Filter to enable the system bindings (meta-!
            prompt and Control-Z suspension.)
    :param enable_search: Filter to enable the search bindings.
    :param enable_open_in_editor: Filter to enable open-in-editor.
    :param enable_open_in_editor: Filter to enable open-in-editor.
    :param enable_extra_page_navigation: Filter for enabling extra page
        navigation. (Bindings for up/down scrolling through long pages, like in
        Emacs or Vi.)
    :param enable_auto_suggest_bindings: Filter to enable fish-style suggestions.
    """
    # Accept both Filters and booleans as input.
    enable_abort_and_exit_bindings = to_filter(enable_abort_and_exit_bindings)
    enable_system_bindings = to_filter(enable_system_bindings)
    enable_search = to_filter(enable_search)
    enable_open_in_editor = to_filter(enable_open_in_editor)
    enable_extra_page_navigation = to_filter(enable_extra_page_navigation)
    enable_auto_suggest_bindings = to_filter(enable_auto_suggest_bindings)

    return merge_key_bindings([
        # Load basic bindings.
        load_basic_bindings(),
        load_mouse_bindings(),

        ConditionalKeyBindings(load_abort_and_exit_bindings(),
                               enable_abort_and_exit_bindings),

        ConditionalKeyBindings(load_basic_system_bindings(),
                               enable_system_bindings),

        # Load emacs bindings.
        load_emacs_bindings(),

        ConditionalKeyBindings(load_emacs_open_in_editor_bindings(),
                               enable_open_in_editor),

        ConditionalKeyBindings(load_emacs_search_bindings(),
                               enable_search),

        ConditionalKeyBindings(load_extra_emacs_page_navigation_bindings(),
                               enable_extra_page_navigation),

        # Load Vi bindings.
        load_vi_bindings(),

        ConditionalKeyBindings(load_vi_open_in_editor_bindings(),
                               enable_open_in_editor),

        ConditionalKeyBindings(load_vi_search_bindings(),
                               enable_search),

        ConditionalKeyBindings(load_extra_vi_page_navigation_bindings(),
                               enable_extra_page_navigation),

        # Suggestion bindings.
        # (This has to come at the end, because the Vi bindings also have an
        # implementation for the "right arrow", but we really want the
        # suggestion binding when a suggestion is available.)
        ConditionalKeyBindings(load_auto_suggestion_bindings(),
                               enable_auto_suggest_bindings),
    ])
