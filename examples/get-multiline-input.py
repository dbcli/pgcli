#!/usr/bin/env python
from __future__ import unicode_literals
from prompt_toolkit import prompt
from prompt_toolkit.token import Token


def continuation_tokens(cli, width):
    " The continuation: display dots before all the following lines. "

    # (make sure that the width of the continuation does not exceed the given
    # width. -- It is the prompt that decides the width of the left margin.)
    return [(Token, '.' * (width - 1) + ' ')]


if __name__ == '__main__':
    print('Press [Meta+Enter] or [Esc] followed by [Enter] to accept input.')
    answer = prompt('Multiline input: ', multiline=True,
                    get_continuation_tokens=continuation_tokens)
    print('You said: %s' % answer)
