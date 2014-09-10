#!/usr/bin/env python
"""
Simple example of a syntax-highlighted HTML input line.
"""
from pygments.lexers import HtmlLexer

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.code import Code
from prompt_toolkit.prompt import Prompt


class HtmlCode(Code):
    lexer = HtmlLexer


class HtmlPrompt(Prompt):
    prompt_text = 'Enter HTML: '


class HtmlCLI(CommandLineInterface):
    code_factory = HtmlCode
    prompt_factory = HtmlPrompt



def main():
    cli = HtmlCLI()

    html_code_obj = cli.read_input()
    print('You said: ' + html_code_obj.text)


if __name__ == '__main__':
    main()
