#!/usr/bin/env python
"""
This is an example of "prompt_toolkit.contrib.shell" which implements a litle
calculator. It has Emacs key bindings, and all the features of the library like
reverse search.

Type for instance::

    > add 4 4
    > sub 4 4
    > sin 3.14

Warning: this example uses "prompt_toolkit.contrib.shell", which we consider
         still experimental.
"""
from pygments.style import Style
from pygments.token import Token

from prompt_toolkit import CommandLineInterface, AbortAction
from prompt_toolkit.contrib.shell.completion import ShellCompleter
from prompt_toolkit.contrib.shell.rules import Any, Sequence, Literal, Variable
from prompt_toolkit.contrib.shell.layout import CompletionHint
from prompt_toolkit.contrib.shell.parse_info import get_parse_info, InvalidCommandException
from prompt_toolkit import Exit
from prompt_toolkit.line import Line
from prompt_toolkit.layout.menus import CompletionMenu

from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt
import math


grammar = Any([
            Sequence([
                        Literal('add', dest='operator'),
                        Variable(placeholder='<number>', dest='var1'),
                        Variable(placeholder='<number>', dest='var2'),
                    ]),
            Sequence([
                        Literal('sub', dest='operator'),
                        Variable(placeholder='<number>', dest='var1'),
                        Variable(placeholder='<number>', dest='var2'),
                    ]),
            Sequence([
                        Literal('div', dest='operator'),
                        Variable(placeholder='<number>', dest='var1'),
                        Variable(placeholder='<number>', dest='var2'),
                    ]),
            Sequence([
                        Literal('mul', dest='operator'),
                        Variable(placeholder='<number>', dest='var1'),
                        Variable(placeholder='<number>', dest='var2'),
                    ]),
            Sequence([
                        Literal('sin', dest='operator'),
                        Variable(placeholder='<number>', dest='var1'),
                    ]),
        ])


class ExampleStyle(Style):
    background_color = None
    styles = {
        Token.Placeholder: "#888888",
        Token.Placeholder.Variable: "#888888",
        Token.Placeholder.Bracket: "bold #ff7777",
        Token.Placeholder.Separator: "#ee7777",
        Token.Aborted:    '#aaaaaa',

        Token.Menu.Completer.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completer.Completion:         'bg:#008888 #ffffff',
        Token.Menu.Completer.ProgressButton:     'bg:#003333',
        Token.Menu.Completer.ProgressBar:        'bg:#00aaaa',
    }


if __name__ == '__main__':
    cli = CommandLineInterface(
        layout=Layout(before_input=DefaultPrompt('Calculate: '),
                      after_input=CompletionHint(grammar),
                      menus=[CompletionMenu()]),
        line=Line(completer=ShellCompleter(grammar)),
        style=ExampleStyle)

    try:
        # REPL loop.
        while True:
            # Read input and parse the result.
            try:
                document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                parse_info = get_parse_info(grammar, document)
            except InvalidCommandException:
                print('Invalid command\n')
                continue

            # For debugging only: show the data structure that we got.
            print('Received data structure: %r' % parse_info)

            try:
                # Get the variables.
                vars = get_parse_info(grammar, document).get_variables()

                var1 = float(vars.get('var1', 0))
                var2 = float(vars.get('var2', 0))

                # Turn the operator string into a function.
                operator = {
                    'add': (lambda a, b: a + b),
                    'sub': (lambda a, b: a - b),
                    'mul': (lambda a, b: a * b),
                    'div': (lambda a, b: a / b),
                    'sin': (lambda a, b: math.sin(a)),
                }[vars['operator']]

                # Execute and print the result.
                print('Result: %s\n' % (operator(var1, var2)))

            except ValueError:
                print('Please enter valid numbers\n')

    except Exit:
        pass
