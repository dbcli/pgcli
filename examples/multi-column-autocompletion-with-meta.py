#!/usr/bin/env python
"""
Autocompletion example that shows meta-information alongside the completions.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit import prompt


animal_completer = WordCompleter([
    'alligator',
    'ant',
    'ape',
    'bat',

    'bear', 'beaver', 'bee', 'bison', 'butterfly', 'cat', 'chicken',
    'crocodile', 'dinosaur', 'dog', 'dolphine', 'dove', 'duck', 'eagle',
    'elephant',
], meta_dict={
    'alligator': 'An alligator is a crocodilian in the genus Alligator of the family Alligatoridae.',
    'ant': 'Ants are eusocial insects of the family Formicidae',
    'ape': 'Apes (Hominoidea) are a branch of Old World tailless anthropoid catarrhine primates ',
    'bat': 'Bats are mammals of the order Chiroptera',
}, ignore_case=True)


def main():
    text = prompt('Give some animals: ', completer=animal_completer, display_completions_in_columns=True)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
