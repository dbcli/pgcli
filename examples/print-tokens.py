#!/usr/bin/env python
"""
Example of printing colored text to the output.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.styles import style_from_dict


def main():
    style = style_from_dict({
        'hello': '#ff0066',
        'world': '#44ff44 italic',
    })
    tokens = [
        ('class:hello', 'Hello '),
        ('class:world', 'World'),
        ('', '\n'),
    ]
    print_tokens(tokens, style=style)


if __name__ == '__main__':
    main()
