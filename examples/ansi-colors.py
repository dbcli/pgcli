#!/usr/bin/env python
"""
Demonstration of all the ANSI colors.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import print_text_fragments


def main():
    nl = ('', '\n')
    tokens = [
        ('underline', 'Foreground colors'), nl,
        ('#ansiblack', '#ansiblack'), nl,
        ('#ansiwhite', '#ansiwhite'), nl,
        ('#ansired', '#ansired'), nl,
        ('#ansigreen', '#ansigreen'), nl,
        ('#ansiyellow', '#ansiyellow'), nl,
        ('#ansiblue', '#ansiblue'), nl,
        ('#ansifuchsia', '#ansifuchsia'), nl,
        ('#ansiturquoise', '#ansiturquoise'), nl,
        ('#ansilightgray', '#ansilightgray'), nl,

        ('#ansidarkgray', '#ansidarkgray'), nl,
        ('#ansidarkred', '#ansidarkred'), nl,
        ('#ansidarkgreen', '#ansidarkgreen'), nl,
        ('#ansibrown', '#ansibrown'), nl,
        ('#ansidarkblue', '#ansidarkblue'), nl,
        ('#ansipurple', '#ansipurple'), nl,
        ('#ansiteal', '#ansiteal'), nl,

        ('underline', 'background colors'), nl,
        ('bg:#ansiblack', '#ansiblack'), nl,
        ('bg:#ansiwhite', '#ansiwhite'), nl,
        ('bg:#ansired', '#ansired'), nl,
        ('bg:#ansigreen', '#ansigreen'), nl,
        ('bg:#ansiyellow', '#ansiyellow'), nl,
        ('bg:#ansiblue', '#ansiblue'), nl,
        ('bg:#ansifuchsia', '#ansifuchsia'), nl,
        ('bg:#ansiturquoise', '#ansiturquoise'), nl,
        ('bg:#ansilightgray', '#ansilightgray'), nl,

        ('bg:#ansidarkgray', '#ansidarkgray'), nl,
        ('bg:#ansidarkred', '#ansidarkred'), nl,
        ('bg:#ansidarkgreen', '#ansidarkgreen'), nl,
        ('bg:#ansibrown', '#ansibrown'), nl,
        ('bg:#ansidarkblue', '#ansidarkblue'), nl,
        ('bg:#ansipurple', '#ansipurple'), nl,
        ('bg:#ansiteal', '#ansiteal'), nl,

        nl,
    ]
    print_text_fragments(tokens)


if __name__ == '__main__':
    main()
