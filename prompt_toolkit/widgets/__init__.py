"""
Collection of reusable components for building full screen applications.
These are higher level abstractions on top of the `prompt_toolkit.layout`
module.

Most of these widgets implement the ``__pt_container__`` method, which makes it
possible to embed these in the layout like any other container.
"""
from __future__ import unicode_literals

from .base import TextArea, Label, Button, Frame, Shadow, Box, VerticalLine, HorizontalLine, RadioList, Checkbox, ProgressBar
from .dialogs import Dialog
from .menus import MenuContainer, MenuItem
from .toolbars import ArgToolbar, CompletionsToolbar, FormattedTextToolbar, SearchToolbar, SystemToolbar, ValidationToolbar

__all__ = [
    # Base.
    'TextArea',
    'Label',
    'Button',
    'Frame',
    'Shadow',
    'Box',
    'VerticalLine',
    'HorizontalLine',
    'RadioList',
    'Checkbox',
    'ProgressBar',

    # Toolbars.
    'ArgToolbar',
    'CompletionsToolbar',
    'FormattedTextToolbar',
    'SearchToolbar',
    'SystemToolbar',
    'ValidationToolbar',

    # Dialogs.
    'Dialog',

    # Menus.
    'MenuContainer',
    'MenuItem',
]
