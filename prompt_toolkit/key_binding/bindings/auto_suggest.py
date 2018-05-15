"""
Key bindings for auto suggestion (for fish-style auto suggestion).
"""
from __future__ import unicode_literals
import re
from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding.key_bindings import KeyBindings
from prompt_toolkit.filters import Condition, emacs_mode

__all__ = [
    'load_auto_suggest_bindings',
]


def load_auto_suggest_bindings():
    """
    Key bindings for accepting auto suggestion text.

    (This has to come after the Vi bindings, because they also have an
    implementation for the "right arrow", but we really want the suggestion
    binding when a suggestion is available.)
    """
    key_bindings = KeyBindings()
    handle = key_bindings.add

    @Condition
    def suggestion_available():
        app = get_app()
        return (app.current_buffer.suggestion is not None and
                app.current_buffer.document.is_cursor_at_the_end)

    @handle('c-f', filter=suggestion_available)
    @handle('c-e', filter=suggestion_available)
    @handle('right', filter=suggestion_available)
    def _(event):
        " Accept suggestion. "
        b = event.current_buffer
        suggestion = b.suggestion

        if suggestion:
            b.insert_text(suggestion.text)

    @handle('escape', 'f', filter=suggestion_available & emacs_mode)
    def _(event):
        " Fill partial suggestion. "
        b = event.current_buffer
        suggestion = b.suggestion

        if suggestion:
            t = re.split(r'(\S+\s+)', suggestion.text)
            b.insert_text(next(x for x in t if x))

    return key_bindings
