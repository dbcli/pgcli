#!/usr/bin/env python
"""
Example of printing colored text to the output.
"""
from __future__ import unicode_literals, print_function
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML, ANSI, FormattedText
from prompt_toolkit.styles import Style

print = print_formatted_text


def main():
    style = Style.from_dict({
        'hello': '#ff0066',
        'world': '#44ff44 italic',
    })

    # Print using a a list of text fragments.
    text_fragments = FormattedText([
        ('class:hello', 'Hello '),
        ('class:world', 'World'),
        ('', '\n'),
    ])
    print(text_fragments, style=style)

    # Print using an HTML object.
    print(HTML(
        '<hello>hello</hello> <world>world</world>\n'),
        style=style)

    # Print using an HTML object with inline styling.
    print(HTML(
        '<style fg="#ff0066">hello</style> '
        '<style fg="#44ff44"><i>world</i></style>\n'))

    # Print using ANSI escape sequences.
    print(ANSI(
        '\x1b[31mhello \x1b[32mworld\n'))


if __name__ == '__main__':
    main()
