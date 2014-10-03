#!/usr/bin/env python
"""
Work in progress version of a PDB prompt.

This is an example of "prompt_toolkit.contrib.shell". It's still very
incomplete, non-functional and experimental. But it shows the direction we're
heading.
"""
from pygments.token import Token, Keyword, Operator, Number, Name, Error, Comment
from pygments.style import Style

from prompt_toolkit import CommandLineInterface, AbortAction
from prompt_toolkit.contrib.shell.completion import ShellCompleter
from prompt_toolkit.contrib.shell.rules import Any, Sequence, Literal, Variable, Repeat
from prompt_toolkit.contrib.shell.layout import CompletionHint
from prompt_toolkit.contrib.shell.parse_info import get_parse_info, InvalidCommandException
from prompt_toolkit import Exit
from prompt_toolkit.line import Line
from prompt_toolkit.layout.menus import CompletionMenu

from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt


grammar = Any([
    Sequence([
        Any([
            Literal('b', dest='cmd_break'),
            Literal('break', dest='cmd_break'),
            Literal('tbreak', dest='tbreak'),
        ]),
        Variable(placeholder='<file:lineno/function>', dest='break_line'),
        Variable(placeholder='<condition>', dest='break_condition'),
    ]),
    Sequence([
        Literal('condition', dest='cmd_condition'),
        Variable(placeholder='<bpnumber>', dest='condition_bpnumber'),
        Variable(placeholder='<str_condition>', dest='condition_str')
    ]),
    Sequence([
        Any([
            Literal('l', dest='cmd_list'),
            Literal('list', dest='cmd_list'),
        ]),
        Variable(placeholder='<first>', dest='list_first'),
        Variable(placeholder='<last>', dest='list_last')
    ]),
    Sequence([
        Literal('debug'),
        Variable(placeholder='<code>'),
    ]),
    Sequence([
        Literal('disable'),
        Variable(placeholder='<bpnumber>'),
    ]),
    Sequence([
        Literal('enable'),
        Repeat(Variable(placeholder='<bpnumber>')),
    ]),
    Sequence([
        Literal('ignore'),
        Variable(placeholder='<bpnumber>'),
        Variable(placeholder='<count>'),
    ]),
    Sequence([
        Literal('run'),
        Repeat(Variable(placeholder='<args>')),
    ]),
    Sequence([
        Literal('alias'),
        Variable(placeholder='<name>'),
        Variable(placeholder='<command>'),
        Repeat(Variable(placeholder='<parameter>')),
    ]),
    Sequence([
        Any([
            Literal('h'),
            Literal('help'),
        ]),
        Variable(placeholder='<command>'),
    ]),
    Sequence([
        Literal('unalias'),
        Variable(placeholder='<name>'),
    ]),
    Sequence([
        Literal('jump'),
        Variable(placeholder='<lineno>'),
    ]),
    Sequence([
        Literal('whatis'),
        Variable(placeholder='<arg>'),
    ]),
    Sequence([
        Literal('pp'),
        Variable(placeholder='<expression>'),
    ]),
    Sequence([
        Literal('p'),
        Variable(placeholder='<expression>'),
    ]),
    Sequence([
        Any([
            Literal('cl'),
            Literal('clear'),
        ]),
        Repeat(Variable(placeholder='<bpnumber>')),
    ]),
    Any([
        Literal('a'),
        Literal('args'),
    ]),
    Any([
        Literal('cont'),
        Literal('continue'),
    ]),
    Any([
        Literal('d'),
        Literal('down'),
    ]),
    Any([
        Literal('exit'),
        Literal('q'),
        Literal('quit'),
    ]),
    Any([
        Literal('n'),
        Literal('next'),
    ]),
    Any([
        Literal('run'),
        Literal('restart'),
    ]),
    Any([
        Literal('unt'),
        Literal('until'),
    ]),
    Any([
        Literal('u'),
        Literal('up'),
    ]),
    Any([
        Literal('r'),
        Literal('return'),
    ]),
    Any([
        Literal('w', dest='where'),
        Literal('where', dest='where'),
        Literal('bt'),
    ]),
    Any([
        Literal('s'),
        Literal('step'),
    ]),
    Literal('commands'),
])


class PdbStyle(Style):
    background_color = None
    styles = {
        # Pdb commands highlighting.
        Token.Placeholder:           "#aa8888",
        Token.Placeholder.Variable:  "#aa8888",
        Token.Placeholder.Bracket:   "bold #ff7777",
        Token.Placeholder.Separator: "#ee7777",
        Token.Aborted:               "#aaaaaa",
        Token.Prompt:                "bold",

        # Python code highlighting.
        Keyword:                      '#ee00ee',
        Operator:                     '#aa6666',
        Number:                       '#ff0000',
        Name:                         '#008800',
        Token.Literal.String:         '#440000',
        Comment:                      '#0000dd',
        Error:                        '#000000 bg:#ff8888',

        # Completion Menu
        Token.Menu.Completions.Completion.Current: 'bg:#00aaaa #000000',
        Token.Menu.Completions.Completion:         'bg:#008888 #ffffff',
        Token.Menu.Completions.ProgressButton:     'bg:#003333',
        Token.Menu.Completions.ProgressBar:        'bg:#00aaaa',
    }


if __name__ == '__main__':
    cli = CommandLineInterface(
        layout=Layout(before_input=DefaultPrompt('(pdb) '),
                      after_input=CompletionHint(grammar),
                      menus=[CompletionMenu()]),
        line=Line(completer=ShellCompleter(grammar)),
        style=PdbStyle)

    try:
        while True:
            document = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)

            try:
                parse_info = get_parse_info(grammar, document)
            except InvalidCommandException:
                print('Invalid command\n')
                continue
            else:
                print(parse_info.get_variables())

    except Exit:
        pass
