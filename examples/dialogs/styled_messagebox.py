#!/usr/bin/env python
"""
Example of a style dialog window.
All dialog shortcuts take a `style` argument in order to apply a custom
styling.

This also demonstrates that the `title` argument can be any kind of formatted
text.
"""
from __future__ import unicode_literals
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.shortcuts.dialogs import message_dialog
from prompt_toolkit.styles import Style


# Custom color scheme.
example_style = Style.from_dict({
    'dialog':             'bg:#88ff88',
    'dialog frame-label': 'bg:#ffffff #000000',
    'dialog.body':        'bg:#000000 #00ff00',
    'dialog.body shadow': 'bg:#00aa00',
})


def main():
    message_dialog(
        title=HTML('<style bg="blue" fg="white">Styled</style> '
                   '<style fg="ansired">dialog</style> window'),
        text='Do you want to continue?\nPress ENTER to quit.',
        style=example_style)


if __name__ == '__main__':
    main()
