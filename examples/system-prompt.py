#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit.contrib.shortcuts import get_input


if __name__ == '__main__':
    print('If you press meta-! or esc-! at the following prompt, you can enter system commands.')
    answer = get_input('Give me some input: ', enable_system_prompt=True)
    print('You said: %s' % answer)
