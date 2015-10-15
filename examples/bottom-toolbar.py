#!/usr/bin/env python
"""
Simple example showing a bottom toolbar.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.styles import PygmentsStyle
from pygments.style import Style
from pygments.token import Token


class TestStyle(Style):
    styles = {
        Token.Toolbar: '#ffffff bg:#333333',
    }


def main():
    def get_bottom_toolbar_tokens(cli):
        return [(Token.Toolbar, ' This is a toolbar. ')]

    text = prompt('Say something: ',
                  get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                  style=PygmentsStyle(TestStyle))
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
