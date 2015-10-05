#!/usr/bin/env python
"""
Demontration of the RETRY option.

Pressing Control-C will not throw a `KeyboardInterrupt` like usual, but instead
the prompt is drawn again.
"""
from __future__ import unicode_literals
from prompt_toolkit import prompt, AbortAction


if __name__ == '__main__':
    answer = prompt('Give me some input: ', on_abort=AbortAction.RETRY)
    print('You said: %s' % answer)
