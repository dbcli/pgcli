#!/usr/bin/env python
"""

Work in progress version of a PDB prompt.

"""

from pygments.style import Style
from pygments.token import Token
from pygments.token import Keyword, Operator, Number, Name, Error, Comment

from prompt_toolkit import CommandLineInterface, AbortAction
from prompt_toolkit.contrib.shell.code import ShellCode
from prompt_toolkit.contrib.shell.prompt import ShellPrompt
from prompt_toolkit.contrib.shell.rules import Any, Sequence, Literal, Variable, Repeat
from prompt_toolkit import Exit
from prompt_toolkit.prompt import Prompt

from prompt_toolkit.contrib.python_input import PythonCode


class PdbCode(ShellCode):
    rule = Any([
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

class PythonOrPdbCode(object):
    def __init__(self, document):
        self._pdb_code = PdbCode(document)
        self._python_code = PythonCode(document, {}, {})
        self._document = document

    @property
    def is_pdb_statement(self):
        if self._document.text == '':
            return True

        try:
            # Try to excess the first parse tree
            bool(self._pdb_code.get_parse_info())
            return True
        except Exception:
            return False

    def __getattr__(self, name):
        if self.is_pdb_statement:
            return getattr(self._pdb_code, name)
        else:
            result = getattr(self._python_code, name)
            return result

    def complete(self):
        # Always return completions for the PDB Shell, if none were found,
        # return completions as it is Python code.
        return self._pdb_code.complete() or self._python_code.complete()


class PdbPrompt(ShellPrompt):
    def _get_lex_result(self):
        return self.code._pdb_code._get_lex_result()

    def get_default_prompt(self):
        yield (Token.Prompt, '(pdb) ')


class PythonPrompt(Prompt):
    def get_default_prompt(self):
        yield (Token.Prompt, '(pdb) ')


class PdbOrPythonprompt(object):
    """
    Create a prompt class that proxies around `PdbPrompt` if the input is valid
    PDB shell input, otherwise proxies around `PythonPrompt`.
    """
    def __init__(self, cli_ref):
        self._pdb_prompt = PdbPrompt(cli_ref)
        self._python_prompt = PythonPrompt(cli_ref)
        self.line = cli_ref().line

    def __getattr__(self, name):
        if self.line.create_code_obj().is_pdb_statement:
            return getattr(self._pdb_prompt, name)
        else:
            return getattr(self._python_prompt, name)


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
        }


class PdbCLI(CommandLineInterface):
    code_factory = PythonOrPdbCode
    prompt_factory = PdbOrPythonprompt

#    # <<
#    code_factory = PdbCode
#    prompt_factory = PdbPrompt
#    # >>

    style = PdbStyle


if __name__ == '__main__':
    cli = PdbCLI()

    try:
        while True:
            code = cli.read_input(on_exit=AbortAction.RAISE_EXCEPTION)

            if code.is_pdb_statement:
                print ('PDB command: %r' % code.get_parse_info().get_variables())
            else:
                print ('Python command: %r' % code.text)

    except Exit:
        pass
