#!/usr/bin/env python
"""
Simple example of a syntax-highlighted HTML input line.
"""
from __future__ import unicode_literals
from pygments.lexers import HtmlLexer
from prompt_toolkit import prompt
from prompt_toolkit.layout.lexers import PygmentsLexer


def main():
    text = prompt('Enter HTML: ', lexer=PygmentsLexer(HtmlLexer))
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
