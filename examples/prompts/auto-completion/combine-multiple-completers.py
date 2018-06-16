#!/usr/bin/env python
"""
Example of multiple individual completers that are combined into one.
"""
from __future__ import unicode_literals

from prompt_toolkit.completion import Completer, merge_completers, WordCompleter
from prompt_toolkit import prompt


animal_completer = WordCompleter([
    'alligator', 'ant', 'ape', 'bat', 'bear', 'beaver', 'bee', 'bison',
    'butterfly', 'cat', 'chicken', 'crocodile', 'dinosaur', 'dog', 'dolphin',
    'dove', 'duck', 'eagle', 'elephant', 'fish', 'goat', 'gorilla', 'kangaroo',
    'leopard', 'lion', 'mouse', 'rabbit', 'rat', 'snake', 'spider', 'turkey',
    'turtle',
], ignore_case=True)

color_completer = WordCompleter([
    'red', 'green', 'blue', 'yellow', 'white', 'black', 'orange', 'gray',
    'pink', 'purple', 'cyan', 'magenta', 'violet',
], ignore_case=True)


def main():
    completer = merge_completers([animal_completer, color_completer])

    text = prompt('Give some animals: ', completer=completer,
                  complete_while_typing=False)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
