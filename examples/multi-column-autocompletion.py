#!/usr/bin/env python
"""
Similar to the autocompletion example. But display all the completions in multiple columns.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.shortcuts import get_input


animal_completer = WordCompleter([
    'alligator',
    'ant',
    'ape',
    'bat',
    'bear',
    'beaver',
    'bee',
    'bison',
    'butterfly',
    'cat',
    'chicken',
    'crocodile',
    'dinosaur',
    'dog',
    'dolphine',
    'dove',
    'duck',
    'eagle',
    'elephant',
    'fish',
    'goat',
    'gorilla',
    'kangoroo',
    'leopard',
    'lion',
    'mouse',
    'rabbit',
    'rat',
    'snake',
    'spider',
    'turkey',
    'turtle',
], ignore_case=True)


def main():
    text = get_input('Give some animals: ', completer=animal_completer, display_completions_in_columns=True)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
