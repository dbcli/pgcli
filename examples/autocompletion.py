#!/usr/bin/env python
"""
Autocompletion example.

Press [Tab] to complete the current word.
- The first Tab press fills in the common part of all completions.
- The second Tab press shows all the completions. (In the menu)
- Any following tab press cycles through all the possible completions.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit import prompt


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
    text = prompt('Give some animals: ', completer=animal_completer)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
