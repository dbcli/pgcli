#!/usr/bin/env python
"""
Demonstration of all the ANSI colors.
"""
from __future__ import unicode_literals, print_function
from prompt_toolkit import print_formatted_text, HTML
from prompt_toolkit.output.defaults import create_output
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles.named_colors import NAMED_COLORS

print = print_formatted_text


def main():
    tokens = FormattedText(
        [('fg:' + name, name + '  ') for name in NAMED_COLORS]
    )

    print(HTML('\n<u>Named colors, use 256 colors.</u>'))
    print(tokens)

    print(HTML('\n<u>Named colors, using True color output.</u>'))
    print(tokens, output=create_output(true_color=True))


if __name__ == '__main__':
    main()
