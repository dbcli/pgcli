#!/usr/bin/env python
"""
Demonstration of all the ANSI colors.
"""
from __future__ import unicode_literals, print_function
from prompt_toolkit import print
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles.named_colors import NAMED_COLORS


def main():
    space = ('', ' ')

    print(HTML('\n<u>Foreground colors</u>'))
    print([
        ('#ansiblack', '#ansiblack'), space,
        ('#ansiwhite', '#ansiwhite'), space,
        ('#ansired', '#ansired'), space,
        ('#ansigreen', '#ansigreen'), space,
        ('#ansiyellow', '#ansiyellow'), space,
        ('#ansiblue', '#ansiblue'), space,
        ('#ansifuchsia', '#ansifuchsia'), space,
        ('#ansiturquoise', '#ansiturquoise'), space,
        ('#ansilightgray', '#ansilightgray'), space,

        ('#ansidarkgray', '#ansidarkgray'), space,
        ('#ansidarkred', '#ansidarkred'), space,
        ('#ansidarkgreen', '#ansidarkgreen'), space,
        ('#ansibrown', '#ansibrown'), space,
        ('#ansidarkblue', '#ansidarkblue'), space,
        ('#ansipurple', '#ansipurple'), space,
        ('#ansiteal', '#ansiteal'), space,
    ])

    print(HTML('\n<u>background colors</u>'))
    print([
        ('bg:#ansiblack', '#ansiblack'), space,
        ('bg:#ansiwhite', '#ansiwhite'), space,
        ('bg:#ansired', '#ansired'), space,
        ('bg:#ansigreen', '#ansigreen'), space,
        ('bg:#ansiyellow', '#ansiyellow'), space,
        ('bg:#ansiblue', '#ansiblue'), space,
        ('bg:#ansifuchsia', '#ansifuchsia'), space,
        ('bg:#ansiturquoise', '#ansiturquoise'), space,
        ('bg:#ansilightgray', '#ansilightgray'), space,

        ('bg:#ansidarkgray', '#ansidarkgray'), space,
        ('bg:#ansidarkred', '#ansidarkred'), space,
        ('bg:#ansidarkgreen', '#ansidarkgreen'), space,
        ('bg:#ansibrown', '#ansibrown'), space,
        ('bg:#ansidarkblue', '#ansidarkblue'), space,
        ('bg:#ansipurple', '#ansipurple'), space,
        ('bg:#ansiteal', '#ansiteal'), space,
    ])


if __name__ == '__main__':
    main()
