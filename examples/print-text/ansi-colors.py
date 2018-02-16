#!/usr/bin/env python
"""
Demonstration of all the ANSI colors.
"""
from __future__ import unicode_literals, print_function
from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import HTML, FormattedText

print = print_formatted_text


def main():
    wide_space = ('', '       ')
    space = ('', ' ')

    print(HTML('\n<u>Foreground colors</u>'))
    print(FormattedText([
        ('ansiblack', 'ansiblack'), wide_space,
        ('ansired', 'ansired'), wide_space,
        ('ansigreen', 'ansigreen'), wide_space,
        ('ansiyellow', 'ansiyellow'), wide_space,
        ('ansiblue', 'ansiblue'), wide_space,
        ('ansimagenta', 'ansimagenta'), wide_space,
        ('ansicyan', 'ansicyan'), wide_space,
        ('ansigray', 'ansigray'), wide_space,
        ('', '\n'),

        ('ansibrightblack', 'ansibrightblack'), space,
        ('ansibrightred', 'ansibrightred'), space,
        ('ansibrightgreen', 'ansibrightgreen'), space,
        ('ansibrightyellow', 'ansibrightyellow'), space,
        ('ansibrightblue', 'ansibrightblue'), space,
        ('ansibrightmagenta', 'ansibrightmagenta'), space,
        ('ansibrightcyan', 'ansibrightcyan'), space,
        ('ansiwhite', 'ansiwhite'), space,
    ]))

    print(HTML('\n<u>Background colors</u>'))
    print(FormattedText([
        ('bg:ansiblack ansiwhite', 'ansiblack'), wide_space,
        ('bg:ansired', 'ansired'), wide_space,
        ('bg:ansigreen', 'ansigreen'), wide_space,
        ('bg:ansiyellow', 'ansiyellow'), wide_space,
        ('bg:ansiblue ansiwhite', 'ansiblue'), wide_space,
        ('bg:ansimagenta', 'ansimagenta'), wide_space,
        ('bg:ansicyan', 'ansicyan'), wide_space,
        ('bg:ansigray', 'ansigray'), wide_space,
        ('', '\n'),

        ('bg:ansibrightblack', 'ansibrightblack'), space,
        ('bg:ansibrightred', 'ansibrightred'), space,
        ('bg:ansibrightgreen', 'ansibrightgreen'), space,
        ('bg:ansibrightyellow', 'ansibrightyellow'), space,
        ('bg:ansibrightblue', 'ansibrightblue'), space,
        ('bg:ansibrightmagenta', 'ansibrightmagenta'), space,
        ('bg:ansibrightcyan', 'ansibrightcyan'), space,
        ('bg:ansiwhite', 'ansiwhite'), space,
    ]))
    print()


if __name__ == '__main__':
    main()
