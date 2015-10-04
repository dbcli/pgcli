#!/usr/bin/env python
"""
Example of a colored prompt.
"""
from __future__ import unicode_literals

from prompt_toolkit import prompt
from pygments.style import Style
from pygments.styles.default import DefaultStyle
from pygments.token import Token


class ExampleStyle(Style):
    styles = DefaultStyle.styles.copy()

    styles.update({
        # User input.
        Token:          '#ff0066',

        # Prompt.
        Token.Username: '#884444',
        Token.At:       '#00aa00',
        Token.Colon:    '#00aa00',
        Token.Pound:    '#00aa00',
        Token.Host:     '#000088 bg:#aaaaff',
        Token.Path:     '#884444 underline',
    })


def get_prompt_tokens(cli):
    return [
        (Token.Username, 'john'),
        (Token.At,       '@'),
        (Token.Host,     'localhost'),
        (Token.Colon,    ':'),
        (Token.Path,     '/user/john'),
        (Token.Pound,    '# '),
    ]


if __name__ == '__main__':
    answer = prompt(get_prompt_tokens=get_prompt_tokens, style=ExampleStyle)
    print('You said: %s' % answer)
