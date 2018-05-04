#!/usr/bin/env python
"""
Similar to the autocompletion example. But display all the completions in multiple columns.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.shortcuts import prompt, CompleteStyle


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
    'dolphin',
    'dove',
    'duck',
    'eagle',
    'elephant',
    'fish',
    'goat',
    'gorilla',
    'kangaroo',
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
    text = prompt('Give some animals: ', completer=animal_completer,
                  complete_style=CompleteStyle.MULTI_COLUMN)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
