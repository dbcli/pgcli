#!/usr/bin/env python
"""
Simple example of a syntax-highlighted HTML input line.
"""
from pygments.lexers import HtmlLexer

from prompt_toolkit.contrib.shortcuts import get_input


def main():
    text = get_input('Enter HTML: ', lexer=HtmlLexer)
    print('You said: ' + text)


if __name__ == '__main__':
    main()
