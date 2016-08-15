#!/usr/bin/env python
"""
Demonstration of all the ANSI colors.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token


def main():
    style = style_from_dict({
        Token.Title: 'underline',

        Token.Black: '#ansiblack',
        Token.White: '#ansiwhite',
        Token.Red: '#ansired',
        Token.Green: '#ansigreen',
        Token.Yellow: '#ansiyellow',
        Token.Blue: '#ansiblue',
        Token.Fuchsia: '#ansifuchsia',
        Token.Turquoise: '#ansiturquoise',
        Token.LightGray: '#ansilightgray',

        Token.DarkGray: '#ansidarkgray',
        Token.DarkRed: '#ansidarkred',
        Token.DarkGreen: '#ansidarkgreen',
        Token.Brown: '#ansibrown',
        Token.DarkBlue: '#ansidarkblue',
        Token.Purple: '#ansipurple',
        Token.Teal: '#ansiteal',

        Token.BgBlack: 'bg:#ansiblack',
        Token.BgWhite: 'bg:#ansiwhite',
        Token.BgRed: 'bg:#ansired',
        Token.BgGreen: 'bg:#ansigreen',
        Token.BgYellow: 'bg:#ansiyellow',
        Token.BgBlue: 'bg:#ansiblue',
        Token.BgFuchsia: 'bg:#ansifuchsia',
        Token.BgTurquoise: 'bg:#ansiturquoise',
        Token.BgLightGray: 'bg:#ansilightgray',

        Token.BgDarkGray: 'bg:#ansidarkgray',
        Token.BgDarkRed: 'bg:#ansidarkred',
        Token.BgDarkGreen: 'bg:#ansidarkgreen',
        Token.BgBrown: 'bg:#ansibrown',
        Token.BgDarkBlue: 'bg:#ansidarkblue',
        Token.BgPurple: 'bg:#ansipurple',
        Token.BgTeal: 'bg:#ansiteal',
    })
    tokens = [
        (Token.Title, 'Foreground colors'), (Token, '\n'),
        (Token.Black, '#ansiblack'), (Token, '\n'),
        (Token.White, '#ansiwhite'), (Token, '\n'),
        (Token.Red, '#ansired'), (Token, '\n'),
        (Token.Green, '#ansigreen'), (Token, '\n'),
        (Token.Yellow, '#ansiyellow'), (Token, '\n'),
        (Token.Blue, '#ansiblue'), (Token, '\n'),
        (Token.Fuchsia, '#ansifuchsia'), (Token, '\n'),
        (Token.Turquoise, '#ansiturquoise'), (Token, '\n'),
        (Token.LightGray, '#ansilightgray'), (Token, '\n'),

        (Token.DarkGray, '#ansidarkgray'), (Token, '\n'),
        (Token.DarkRed, '#ansidarkred'), (Token, '\n'),
        (Token.DarkGreen, '#ansidarkgreen'), (Token, '\n'),
        (Token.Brown, '#ansibrown'), (Token, '\n'),
        (Token.DarkBlue, '#ansidarkblue'), (Token, '\n'),
        (Token.Purple, '#ansipurple'), (Token, '\n'),
        (Token.Teal, '#ansiteal'), (Token, '\n'),

        (Token.Title, 'Background colors'), (Token, '\n'),
        (Token.BgBlack, '#ansiblack'), (Token, '\n'),
        (Token.BgWhite, '#ansiwhite'), (Token, '\n'),
        (Token.BgRed, '#ansired'), (Token, '\n'),
        (Token.BgGreen, '#ansigreen'), (Token, '\n'),
        (Token.BgYellow, '#ansiyellow'), (Token, '\n'),
        (Token.BgBlue, '#ansiblue'), (Token, '\n'),
        (Token.BgFuchsia, '#ansifuchsia'), (Token, '\n'),
        (Token.BgTurquoise, '#ansiturquoise'), (Token, '\n'),
        (Token.BgLightGray, '#ansilightgray'), (Token, '\n'),

        (Token.BgDarkGray, '#ansidarkgray'), (Token, '\n'),
        (Token.BgDarkRed, '#ansidarkred'), (Token, '\n'),
        (Token.BgDarkGreen, '#ansidarkgreen'), (Token, '\n'),
        (Token.BgBrown, '#ansibrown'), (Token, '\n'),
        (Token.BgDarkBlue, '#ansidarkblue'), (Token, '\n'),
        (Token.BgPurple, '#ansipurple'), (Token, '\n'),
        (Token.BgTeal, '#ansiteal'), (Token, '\n'),

        (Token, '\n'),
    ]
    print_tokens(tokens, style=style)


if __name__ == '__main__':
    main()
