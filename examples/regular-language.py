#!/usr/bin/env python
"""
This is an example of "prompt_toolkit.contrib.regular_languages" which
implements a litle calculator.

Type for instance::

    > add 4 4
    > sub 4 4
    > sin 3.14

This example shows how you can define the grammar of a regular language and how
to use variables in this grammar with completers and tokens attached.
"""
from __future__ import unicode_literals
from prompt_toolkit.contrib.completers import WordCompleter

from prompt_toolkit import prompt
from prompt_toolkit.contrib.regular_languages.compiler import compile
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter
from prompt_toolkit.contrib.regular_languages.lexer import GrammarLexer
from prompt_toolkit.layout.lexers import SimpleLexer
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token

import math


operators1 = ['add', 'sub', 'div', 'mul']
operators2 = ['sqrt', 'log', 'sin', 'ln']


def create_grammar():
    return compile("""
        (\s*  (?P<operator1>[a-z]+)   \s+   (?P<var1>[0-9.]+)   \s+   (?P<var2>[0-9.]+)   \s*) |
        (\s*  (?P<operator2>[a-z]+)   \s+   (?P<var1>[0-9.]+)   \s*)
    """)


example_style = style_from_dict({
    Token.Operator:       '#33aa33 bold',
    Token.Number:         '#aa3333 bold',

    Token.TrailingInput: 'bg:#662222 #ffffff',
})


if __name__ == '__main__':
    g = create_grammar()

    lexer = GrammarLexer(g, lexers={
        'operator1': SimpleLexer(Token.Operator),
        'operator2': SimpleLexer(Token.Operator),
        'var1': SimpleLexer(Token.Number),
        'var2': SimpleLexer(Token.Number),
    })

    completer = GrammarCompleter(g, {
        'operator1': WordCompleter(operators1),
        'operator2': WordCompleter(operators2),
    })


    try:
        # REPL loop.
        while True:
            # Read input and parse the result.
            text = prompt('Calculate: ', lexer=lexer, completer=completer,
                          style=example_style)
            m = g.match(text)
            if m:
                vars = m.variables()
            else:
                print('Invalid command\n')
                continue

            print(vars)
            if vars.get('operator1') or vars.get('operator2'):
                try:
                    var1 = float(vars.get('var1', 0))
                    var2 = float(vars.get('var2', 0))
                except ValueError:
                    print('Invalid command (2)\n')
                    continue

                # Turn the operator string into a function.
                operator = {
                    'add': (lambda a, b: a + b),
                    'sub': (lambda a, b: a - b),
                    'mul': (lambda a, b: a * b),
                    'div': (lambda a, b: a / b),
                    'sin': (lambda a, b: math.sin(a)),
                }[vars.get('operator1') or vars.get('operator2')]

                # Execute and print the result.
                print('Result: %s\n' % (operator(var1, var2)))

            elif vars.get('operator2'):
                print('Operator 2')

    except EOFError:
        pass
