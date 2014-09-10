#!/usr/bin/env python
"""

Work in progress.

Alternative for a shell (like Bash).

"""

from pygments.style import Style
from pygments.token import Token

from prompt_toolkit import CommandLineInterface, AbortAction
from prompt_toolkit.contrib.shell.code import ShellCode
from prompt_toolkit.contrib.shell.completers import Path
from prompt_toolkit.contrib.shell.prompt import ShellPrompt
from prompt_toolkit.contrib.shell.rules import Any, Sequence, Literal, Repeat, Variable
from prompt_toolkit import Exit


class OurGitCode(ShellCode):
    rule = Any([
            Sequence([
                Any([
                    Literal('cd'),
                    Literal('ls'),
                    Literal('pushd'),
                    ]),
                    Variable(Path, placeholder='<directory>') ]),

            Literal('pwd'),
            Sequence([Literal('rm'), Variable(Path, placeholder='<file>') ]),
            Sequence([Literal('cp'), Variable(Path, placeholder='<from>'), Variable(Path, placeholder='<to>') ]),
            #Sequence([Literal('cp'), Repeat(Variable(Path, placeholder='<from>')), Variable(Path, placeholder='<to>') ]),
            Sequence([Literal('git'), Repeat(
                Any([
                    #Sequence([]),
                    Literal('--version'),
                    Sequence([Literal('-c'), Variable(placeholder='<name>=<value>')]),
                    Sequence([Literal('--exec-path'), Variable(Path, placeholder='<path>')]),
                    Literal('--help'),
                    ])
                ),
                Any([
                    Sequence([ Literal('checkout'), Variable(placeholder='<commit>') ]),
                    Sequence([ Literal('clone'), Variable(placeholder='<repository>') ]),
                    Sequence([ Literal('diff'), Variable(placeholder='<commit>') ]),
                    ]),
                ]),
            Sequence([Literal('echo'), Repeat(Variable(placeholder='<text>')), ]),
    ])



class ExampleStyle(Style):
    background_color = None
    styles = {
            Token.Placeholder: "#aa8888",
            Token.Placeholder.Variable: "#aa8888",
            Token.Placeholder.Bracket: "bold #ff7777",
            Token.Placeholder.Separator: "#ee7777",
#            A.Path:    '#0044aa',
#            A.Param:   '#ff00ff',
            Token.Aborted:    '#aaaaaa',
        }


class ExampleCLI(CommandLineInterface):
    code_factory = OurGitCode
    prompt_factory = ShellPrompt

    style = ExampleStyle


if __name__ == '__main__':
    cli = ExampleCLI()

    try:
        while True:
            shell_code = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)
            parse_info = shell_code.get_parse_info()

            print ('You said: %r' % parse_info)
            print(parse_info.get_variables())

    except Exit:
        pass
