#!/usr/bin/env python
"""
Simple example of a syntax-highlighted HTML input line.
"""
from pygments.lexers import HtmlLexer

from prompt_toolkit import CommandLineInterface
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.prompt import DefaultPrompt


def main():
    cli = CommandLineInterface(layout=Layout(
        before_input=DefaultPrompt('Enter HTML: '),
        lexer=HtmlLexer))

    html_code_obj = cli.read_input()
    print('You said: ' + html_code_obj.text)


if __name__ == '__main__':
    main()
