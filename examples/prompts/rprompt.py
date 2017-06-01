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
from prompt_toolkit.layout.formatted_text import HTML, ANSI

example_style = Style.from_dict({
    # The 'rprompt' gets by default the 'rprompt' class. We can use this
    # for the styling.
    'rprompt': 'bg:#ff0066 #ffffff',
})


def get_rprompt_text():
    return [
        ('', ' '),
        ('underline', '<rprompt>'),
        ('', ' '),
    ]


def main():
    # Option 1: pass a string to 'rprompt':
    answer = prompt('> ', rprompt=' <rprompt> ', style=example_style)
    print('You said: %s' % answer)

    # Option 2: pass HTML:
    answer = prompt('> ', rprompt=HTML(' <u>&lt;rprompt&gt;</u> '), style=example_style)
    print('You said: %s' % answer)

    # Option 3: pass ANSI:
    answer = prompt('> ', rprompt=ANSI(' \x1b[4m<rprompt>\x1b[0m '), style=example_style)
    print('You said: %s' % answer)

    # Option 4: Pass a callable. (This callable can either return plain text,
    #           an HTML object, an ANSI object or a list of (style, text)
    #           tuples.
    answer = prompt('> ', rprompt=get_rprompt_text, style=example_style)
    print('You said: %s' % answer)


if __name__ == '__main__':
    main()
