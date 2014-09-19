#!/usr/bin/env python
"""
This is an example of "prompt_toolkit.contrib.shell" which implements a litle
calculator. It has Emacs key bindings, and all the features of the library like
reverse search.

Type for instance::

    > add 4 4
    > sub 4 4
    > sin 3.14
"""
from pygments.style import Style
from pygments.token import Token

from prompt_toolkit import CommandLineInterface, AbortAction
from prompt_toolkit.contrib.shell.code import ShellCode, InvalidCommandException
from prompt_toolkit.contrib.shell.prompt import ShellPrompt
from prompt_toolkit.contrib.shell.rules import Any, Sequence, Literal, Variable
from prompt_toolkit import Exit

import math


class CalculatorCode(ShellCode):
    rule = Any([
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
        Token.Placeholder: "#aa8888",
        Token.Placeholder.Variable: "#aa8888",
        Token.Placeholder.Bracket: "bold #ff7777",
        Token.Placeholder.Separator: "#ee7777",
        Token.Aborted:    '#aaaaaa',
    }


class CalculatorCLI(CommandLineInterface):
    code_factory = CalculatorCode
    prompt_factory = ShellPrompt

    style = ExampleStyle


if __name__ == '__main__':
    cli = CalculatorCLI()

    try:
        # REPL loop.
        while True:
            # Read input and parse the result.
            try:
                calculator_code = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                parse_info = calculator_code.get_parse_info()
            except InvalidCommandException:
                print('Invalid command\n')
                continue

            # For debugging only: show the data structure that we got.
            print('Received data structure: %r' % parse_info)

            try:
                # Get the variables.
                vars = parse_info.get_variables()

                var1 = float(vars.get('var1', 0))
                var2 = float(vars.get('var2', 0))

                # Turn the operator string into a function.
                operator = {
                    'add': (lambda a, b: a + b),
                    'sub': (lambda a, b: a - b),
                    'mul': (lambda a, b: a * b),
                    'div': (lambda a, b: a - b),
                    'sin': (lambda a, b: math.sin(a)),
                }[vars['operator']]

                # Execute and print the result.
                print('Result: %s\n' % (operator(var1, var2)))

            except ValueError:
                print('Please enter valid numbers\n')

    except Exit:
        pass
