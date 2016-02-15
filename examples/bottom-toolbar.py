#!/usr/bin/env python
"""
Simple example showing a bottom toolbar.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token


test_style = style_from_dict({
    Token.Toolbar: '#ffffff bg:#333333',
})


def main():
    def get_bottom_toolbar_tokens(cli):
        return [(Token.Toolbar, ' This is a toolbar. ')]

    text = prompt('Say something: ',
                  get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                  style=test_style)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
