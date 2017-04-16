#!/usr/bin/env python
"""
Simple example showing a bottom toolbar.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style


test_style = Style.from_dict({
    'toolbar': '#ffffff bg:#333333',
})


def main():
    def get_bottom_toolbar_tokens(app):
        return [('class:toolbar', ' This is a toolbar. ')]

    text = prompt('Say something: ',
                  get_bottom_toolbar_tokens=get_bottom_toolbar_tokens,
                  style=test_style)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
