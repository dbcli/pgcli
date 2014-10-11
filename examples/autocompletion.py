#!/usr/bin/env python
"""
Autocompletion example.

Press [Tab] to complete the current word.
- The first Tab press fills in the common part of all completions.
- The second Tab press shows all the completions. (In the menu)
- Any following tab press cycles through all the possible completions.
"""
from __future__ import unicode_literals

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.line import Line
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionsMenu
from prompt_toolkit.contrib.completers import WordCompleter

from pygments.token import Token
from pygments.style import Style


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


class AnimalStyle(Style):
    styles = {
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion:         'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton:     'bg:#003333',
        Token.Menu.Completions.ProgressBar:        'bg:#00aaaa',
    }


def main():
    cli = CommandLineInterface(
        style=AnimalStyle,
        layout=Layout(before_input=DefaultPrompt('Give some animals: '),
                      menus=[CompletionsMenu()]),
        line=Line(completer=animal_completer),
        create_async_autocompleters=True)

    print('Press tab to complete')
    code_obj = cli.read_input()
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
