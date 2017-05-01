#!/usr/bin/env python
"""
Example of a 'dynamic' prompt. On that shows the current time in the prompt.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import prompt
import datetime


def get_prompt(app):
    " Tokens to be shown before the prompt. "
    now = datetime.datetime.now()
    return [
        ('bg:#008800 #ffffff', '%s:%s:%s' % (now.hour, now.minute, now.second)),
        ('bg:cornsilk fg:maroon', ' Enter something: ')
    ]


def main():
    result = prompt(get_prompt, refresh_interval=.5)
    print('You said: %s' % result)


if __name__ == '__main__':
    main()
