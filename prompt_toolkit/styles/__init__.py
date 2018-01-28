"""
Styling for prompt_toolkit applications.
"""
from __future__ import unicode_literals, absolute_import

from .base import Attrs, DEFAULT_ATTRS, ANSI_COLOR_NAMES, BaseStyle, DummyStyle, DynamicStyle
from .defaults import default_ui_style, default_pygments_style
from .style import Style, Priority, merge_styles
from .pygments import style_from_pygments_cls, style_from_pygments_dict, pygments_token_to_classname
from .named_colors import NAMED_COLORS


__all__ = [
    # Base.
    'Attrs',
    'DEFAULT_ATTRS',
    'ANSI_COLOR_NAMES',
    'BaseStyle',
    'DummyStyle',
    'DynamicStyle',

    # Defaults.
    'default_ui_style',
    'default_pygments_style',

    # Style.
    'Style',
    'Priority',
    'merge_styles',

    # Pygments.
    'style_from_pygments_cls',
    'style_from_pygments_dict',
    'pygments_token_to_classname',

    # Named colors.
    'NAMED_COLORS',
]
