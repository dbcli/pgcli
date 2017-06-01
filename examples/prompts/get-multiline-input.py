#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt


def prompt_continuation(width):
    " The continuation: display dots before all the following lines. "

    # (make sure that the width of the continuation does not exceed the given
    # width. -- It is the prompt that determines the width of the left margin.)
    return [('', '.' * (width - 1) + ' ')]


if __name__ == '__main__':
    print('Press [Meta+Enter] or [Esc] followed by [Enter] to accept input.')
    answer = prompt('Multiline input: ', multiline=True,
                    prompt_continuation=prompt_continuation)
    print('You said: %s' % answer)
