#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt


if __name__ == '__main__':
    def get_title():
        return 'This is the title'

    answer = prompt('Give me some input: ', get_title=get_title)
    print('You said: %s' % answer)
