#!/usr/bin/env python
"""
Example of a colored prompt.
"""
from __future__ import unicode_literals

from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.layout.formatted_text import HTML, ANSI


style = Style.from_dict({
    # Default style.
    '':          '#ff0066',

    # Prompt.
    'username': '#884444 italic',
    'at':       '#00aa00',
    'colon':    '#00aa00',
    'pound':    '#00aa00',
    'host':     '#000088 bg:#aaaaff',
    'path':     '#884444 underline',

    # Make a selection reverse/underlined.
    # (Use Control-Space to select.)
    'selected-text': 'reverse underline',
})


def example_1():
    """
    Style and list of (style, text) tuples.
    """
    # Not that we can combine class names and inline styles.
    prompt_fragments = [
        ('class:username', 'john'),
        ('class:at',       '@'),
        ('class:host',     'localhost'),
        ('class:colon',    ':'),
        ('class:path',     '/user/john'),
        ('bg:#00aa00 #ffffff',    '#'),
        ('',  ' '),
    ]

    answer = prompt(prompt_fragments, style=style)
    print('You said: %s' % answer)


def example_2():
    """
    Using HTML for the formatting.
    """
    answer = prompt(HTML(
        '<username>john</username><at>@</at>'
        '<host>localhost</host>'
        '<colon>:</colon>'
        '<path>/user/john</path>'
        '<style bg="#00aa00" fg="#ffffff">#</style> '), style=style)
    print('You said: %s' % answer)


def example_3():
    """
    Using ANSI for the formatting.
    """
    answer = prompt(ANSI(
        '\x1b[31mjohn\x1b[0m@'
        '\x1b[44mlocalhost\x1b[0m:'
        '\x1b[4m/user/john\x1b[0m'
        '# '))
    print('You said: %s' % answer)



if __name__ == '__main__':
    example_1()
    example_2()
    example_3()
