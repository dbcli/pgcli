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
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.line import Line
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.menus import CompletionMenu

from pygments.token import Token
from pygments.style import Style


class AnimalCompleter(Completer):
    animals = [
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
    ]

    def get_completions(self, document):
        word_before_cursor = document.get_word_before_cursor()

        for a in self.animals:
            if a.startswith(word_before_cursor):
                yield Completion(a, -len(word_before_cursor))


class AnimalStyle(Style):
    styles = {
        Token.CompletionMenu.Completion.Current: 'bg:#00aaaa #000000',
        Token.CompletionMenu.Completion:         'bg:#008888 #ffffff',
        Token.CompletionMenu.ProgressButton:     'bg:#003333',
        Token.CompletionMenu.ProgressBar:        'bg:#00aaaa',
    }


def main():
    cli = CommandLineInterface(style=AnimalStyle,
                   layout=Layout(before_input=DefaultPrompt('Give some animals: '),
                                 menus=[CompletionMenu()]),
                   line=Line(completer=AnimalCompleter()),
                   create_async_autocompleters=True,
            )

    print('Press tab to complete')
    code_obj = cli.read_input()
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
