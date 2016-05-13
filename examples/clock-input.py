#!/usr/bin/env python
"""
Example of a 'dynamic' prompt. On that shows the current time in the prompt.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.token import Token
import datetime


def get_prompt_tokens(cli):
    " Tokens to be shown before the prompt. "
    now = datetime.datetime.now()
    return [
        (Token.Prompt, '%s:%s:%s' % (now.hour, now.minute, now.second)),
        (Token.Prompt, ' Enter something: ')
    ]


def main():
    result = prompt(get_prompt_tokens=get_prompt_tokens, refresh_interval=.5)
    print('You said: %s' % result)


if __name__ == '__main__':
    main()
