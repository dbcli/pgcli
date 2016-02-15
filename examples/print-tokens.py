#!/usr/bin/env python
"""
Example of printing colored text to the output.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token


def main():
    style = style_from_dict({
        Token.Hello: '#ff0066',
        Token.World: '#44ff44 italic',
    })
    tokens = [
        (Token.Hello, 'Hello '),
        (Token.World, 'World'),
        (Token, '\n'),
    ]
    print_tokens(tokens, style=style)


if __name__ == '__main__':
    main()
