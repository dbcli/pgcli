#!/usr/bin/env python
"""
A few examples of displaying a bottom toolbar.

The ``prompt`` function takes a ``bottom_toolbar`` attribute.
This can be any kind of formatted text (plain text, HTML or ANSI), or
it can be a callable that takes an App and returns an of these.

The bottom toolbar will always receive the style 'bottom-toolbar', and the text
inside will get 'bottom-toolbar.text'. These can be used to change the default
style.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML, ANSI
import time


def main():
    # Example 1: fixed text.
    text = prompt('Say something: ', bottom_toolbar='This is a toolbar')
    print('You said: %s' % text)

    # Example 2: fixed text from a callable:
    def get_toolbar():
        return 'Bottom toolbar: time=%r' % time.time()

    text = prompt('Say something: ', bottom_toolbar=get_toolbar,
                  refresh_interval=.5)
    print('You said: %s' % text)

    # Example 3: Using HTML:
    text = prompt('Say something: ', bottom_toolbar=HTML(
        '(html) <b>This</b> <u>is</u> a <style bg="ansired">toolbar</style>'))
    print('You said: %s' % text)

    # Example 4: Using ANSI:
    text = prompt('Say something: ', bottom_toolbar=ANSI(
        '(ansi): \x1b[1mThis\x1b[0m \x1b[4mis\x1b[0m a \x1b[91mtoolbar'))
    print('You said: %s' % text)

    # Example 5: styling differently.
    style = Style.from_dict({
        'bottom-toolbar':      '#aaaa00 bg:#ff0000',
        'bottom-toolbar.text': '#aaaa44 bg:#aa4444',
    })

    text = prompt('Say something: ', bottom_toolbar='This is a toolbar',
                  style=style)
    print('You said: %s' % text)

    # Example 6: Using a list of tokens.
    def get_bottom_toolbar():
        return [
            ('', ' '),
            ('bg:#ff0000 fg:#000000', 'This'),
            ('', ' is a '),
            ('bg:#ff0000 fg:#000000', 'toolbar'),
            ('', '. '),
        ]

    text = prompt('Say something: ', bottom_toolbar=get_bottom_toolbar)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
