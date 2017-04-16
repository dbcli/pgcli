#!/usr/bin/env python
"""
Example of a colored prompt.
"""
from __future__ import unicode_literals

from prompt_toolkit import prompt
from prompt_toolkit.styles import Style


example_style = Style.from_dict({
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


def get_prompt_fragments(app):
    # Not that we can combine class names and inline styles.
    return [
        ('class:username', 'john'),
        ('class:at',       '@'),
        ('class:host',     'localhost'),
        ('class:colon',    ':'),
        ('class:path',     '/user/john'),
        ('bg:#00aa00 #ffffff',    '#'),
        ('',    ' '),
    ]


if __name__ == '__main__':
    answer = prompt(get_prompt_fragments=get_prompt_fragments, style=example_style)
    print('You said: %s' % answer)
