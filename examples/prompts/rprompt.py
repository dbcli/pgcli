#!/usr/bin/env python
"""
Example of a right prompt. This is an additional prompt that is displayed on
the right side of the terminal. It will be hidden automatically when the input
is long enough to cover the right side of the terminal.

This is similar to RPROMPT is Zsh.
"""
from __future__ import unicode_literals

from prompt_toolkit import prompt
from prompt_toolkit.styles import Style

example_style = Style.from_dict({
    'rprompt': 'bg:#ff0066 #ffffff',
})


def get_rprompt_tokens(app):
    return [
        ('', ' '),
        ('class:rprompt', '<rprompt>'),
    ]


if __name__ == '__main__':
    answer = prompt('> ', get_rprompt_tokens=get_rprompt_tokens, style=example_style)
    print('You said: %s' % answer)
