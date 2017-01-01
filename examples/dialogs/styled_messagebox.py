#!/usr/bin/env python
"""
Example of a style dialog window.
All dialog shortcuts take a `style` argument in order to apply a custom
styling.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.dialogs import message_dialog
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token


# Custom color scheme.
example_style = style_from_dict({
    Token.Dialog:        'bg:#88ff88',
    Token.Dialog.Body:   'bg:#000000 #00ff00',
    Token.Dialog | Token.Frame.Label: 'bg:#ffffff #000000',
    Token.Dialog.Body | Token.Shadow: 'bg:#00aa00',
})


def main():
    message_dialog(
        title='Styled dialog window',
        text='Do you want to continue?\nPress ENTER to quit.',
        style=example_style)


if __name__ == '__main__':
    main()
