#!/usr/bin/env python
"""
Demonstration of all the ANSI colors.
"""
from __future__ import unicode_literals, print_function
from prompt_toolkit import print, HTML
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.styles.named_colors import NAMED_COLORS


def main():
    nl = ('', '\n')
    tokens = [('fg:' + name, name + '  ') for name in NAMED_COLORS]

    print(HTML('\n<u>Named colors, use 256 colors.</u>'))
    print(tokens)

    print(HTML('\n<u>Named colors, using True color output.</u>'))
    print(tokens, output=create_output(true_color=True))


if __name__ == '__main__':
    main()
