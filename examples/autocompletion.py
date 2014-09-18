#!/usr/bin/env python
"""
Autocompletion example.

Press [Tab] to complete the current word.
"""
from __future__ import unicode_literals

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.code import Code, Completion


class AnimalCode(Code):
    animals = [
        'cat',
        'dinosaur',
        'dog',
        'dolphine',
        'dove',
        'duck',
        'eagle',
        'elephant',
        'lion',
        'rabbit',
        'rat',
        'snake',
        'spider',
        'turkey',
        'turtle',
    ]

    def get_completions(self):
        word_before_cursor = self.document.get_word_before_cursor()

        for a in self.animals:
            if a.startswith(word_before_cursor):
                yield Completion(a, -len(word_before_cursor))


class AnimalCLI(CommandLineInterface):
    code_factory = AnimalCode


def main():
    cli = AnimalCLI()

    code_obj = cli.read_input()
    print('You said: ' + code_obj.text)


if __name__ == '__main__':
    main()
