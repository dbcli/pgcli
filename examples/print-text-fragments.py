#!/usr/bin/env python
"""
Example of printing colored text to the output.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import print_text_fragments
from prompt_toolkit.styles import Style


def main():
    style = Style.from_dict({
        'hello': '#ff0066',
        'world': '#44ff44 italic',
    })
    tokens = [
        ('class:hello', 'Hello '),
        ('class:world', 'World'),
        ('', '\n'),
    ]
    print_text_fragments(tokens, style=style)


if __name__ == '__main__':
    main()
