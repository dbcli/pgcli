#!/usr/bin/env python
"""
Simple example showing a bottom toolbar.
"""
from prompt_toolkit.contrib.shortcuts import get_input
from pygments.token import Token
from pygments.style import Style


class TestStyle(Style):
    styles = {
        Token.Toolbar: '#ffffff bg:#333333',
    }

def main():
    def get_bottom_toolbar_tokens(cli):
        return [(Token.Toolbar, ' This is a toolbar. ')]

    text = get_input('Say something: ',
                     get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                     style=TestStyle)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
