"""
Many places in prompt_toolkit can take either plain text, or formatted text.
For instance the :func:`~prompt_toolkit.shortcuts.prompt` function takes either
plain text or formatted text for the prompt. The
:class:`~prompt_toolkit.layout.FormattedTextControl` can also take either plain
text or formatted text.

In any case, there is an input that can either be just plain text (a string),
an :class:`.HTML` object, an :class:`.ANSI` object or a sequence of
`(style_string, text)` tuples. The :func:`.to_formatted_text` conversion
function takes any of these and turns all of them into such a tuple sequence.
"""
from __future__ import unicode_literals
from .base import to_formatted_text, is_formatted_text, Template, merge_formatted_text, FormattedText
from .html import HTML
from .ansi import ANSI
from .pygments import PygmentsTokens
from .utils import fragment_list_len, fragment_list_width, fragment_list_to_text, split_lines

__all__ = [
    # Base.
    'to_formatted_text',
    'is_formatted_text',
    'Template',
    'merge_formatted_text',
    'FormattedText',

    # HTML.
    'HTML',

    # ANSI.
    'ANSI',

    # Pygments.
    'PygmentsTokens',

    # Utils.
    'fragment_list_len',
    'fragment_list_width',
    'fragment_list_to_text',
    'split_lines',
]
