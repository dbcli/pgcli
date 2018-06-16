#!/usr/bin/env python
"""
Example of `accept_default`, a way to automatically accept the input that the
user typed without allowing him/her to edit it.

This should display the prompt with all the formatting like usual, but not
allow any editing.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt, HTML


if __name__ == '__main__':
    answer = prompt(
        HTML('<b>Type <u>some input</u>: </b>'),
        accept_default=True, default='test')

    print('You said: %s' % answer)
