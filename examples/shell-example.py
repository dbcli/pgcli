#!/usr/bin/env python
"""
Alternative for a shell (like Bash).

Warning: This is work in progress!
For now we use this to test which functionality/flexibility we need in
'contrib.shell'. APIs can change a lot over there...
"""
import os

from pygments.style import Style
from pygments.token import Token

from prompt_toolkit import CommandLineInterface, AbortAction
from prompt_toolkit import Exit
from prompt_toolkit.contrib.shell.completers import Path, Directory, ExecutableInPATH
from prompt_toolkit.contrib.shell.completion import ShellCompleter
from prompt_toolkit.contrib.shell.layout import CompletionHint
from prompt_toolkit.contrib.shell.parse_info import get_parse_info, InvalidCommandException
from prompt_toolkit.contrib.shell.rules import Any, Sequence, Literal, Repeat, Variable
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.menus import CompletionMenu
from prompt_toolkit.layout.prompt import DefaultPrompt
from prompt_toolkit.layout.toolbars import Toolbar
from prompt_toolkit.line import Line


grammar = Any([
        Sequence([
            Any([
                Literal('cd', dest='command'),
                #Literal('ls', dest='command'),
                #Literal('rm', dest='command'),
                #Literal('pwd', dest='command'),
                Literal('pushd', dest='commnd'),
                ]),
            Variable(Directory, placeholder='<directory>', dest='directory')]),

        Sequence([
            Variable(ExecutableInPATH, placeholder='<executable>', dest='executable'),
            Repeat(Variable(Path, 'param'))
        ]),

        #Sequence([
        #    Literal('cp'),
        #    Variable(Path, placeholder='<from>'),
        #    Variable(Path, placeholder='<to>')
        #]),
        # Sequence([Literal('git'), Repeat(
        #     Any([
        #         Literal('--version'),
        #         Sequence([Literal('-c'), Variable(placeholder='<name>=<value>')]),
        #         Sequence([Literal('--exec-path'), Variable(Path, placeholder='<path>')]),
        #         Literal('--help'),
        #         ])
        #     ),
        #     Any([
        #         Sequence([Literal('checkout'), Variable(placeholder='<commit>')]),
        #         Sequence([Literal('clone'), Variable(placeholder='<repository>')]),
        #         Sequence([Literal('diff'), Variable(placeholder='<commit>')]),
        #         ]),
        #     ]),
    ])


class ExampleStyle(Style):
    background_color = None
    styles = {
        Token.Placeholder:           "#aa8888",
        Token.Placeholder.Variable:  "#aa8888",
        Token.Placeholder.Bracket:   "bold #ff7777",
        Token.Placeholder.Separator: "#ee7777",
        Token.Aborted:               '#aaaaaa',

        Token.Menu.Completer.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completer.Completion:         'bg:#008888 #ffffff',
        Token.Menu.Completer.ProgressButton:     'bg:#003333',
        Token.Menu.Completer.ProgressBar:        'bg:#00aaaa',

        Token.Prompt.BeforeInput: '#105055 bold',
        Token.StatusBar: 'bg:#105055 #ffffff',
    }


class StatusToolbar(Toolbar):
    """
    Status toolbar showing the current location.
    """
    def __init__(self):
        super(StatusToolbar, self).__init__(Token.StatusBar)

    def get_tokens(self, cli, width):
        return [
            (self.token, ' '),
            (self.token, os.getcwd())
        ]


if __name__ == '__main__':
    cli = CommandLineInterface(
        layout=Layout(before_input=DefaultPrompt('Shell> '),
                      #after_input=CompletionHint(grammar),
                      menus=[CompletionMenu()],
                      bottom_toolbars=[
                          StatusToolbar()
                      ]),
        line=Line(completer=ShellCompleter(grammar)),
        style=ExampleStyle)

    try:
        while True:
            try:
                document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
                parse_info = get_parse_info(grammar, document)
            except InvalidCommandException:
                os.system(document.text)
                continue
            else:
                params = parse_info.get_variables()

                if params.get('command', '') == 'cd':
                    # Handle 'cd' command.
                    try:
                        os.chdir(params['directory'])
                    except OSError as e:
                        print(str(e))
                else:
                    os.system(document.text)

    except Exit:
        pass
