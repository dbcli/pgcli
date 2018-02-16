#!/usr/bin/env python
"""
A simple progress bar, visualised with rainbow colors (for fun).
"""
from __future__ import unicode_literals
from prompt_toolkit.output import ColorDepth
from prompt_toolkit.shortcuts.progress_bar import progress_bar, formatters
from prompt_toolkit.shortcuts.prompt import confirm
import time


def main():
    true_color = confirm('Yes true colors? ')

    custom_formatters = [
        formatters.Label(),
        formatters.Text(' '),
        formatters.Rainbow(formatters.Bar()),
        formatters.Text(' left: '),
        formatters.Rainbow(formatters.TimeLeft()),
    ]

    if true_color:
        color_depth = ColorDepth.DEPTH_24_BIT
    else:
        color_depth = ColorDepth.DEPTH_8_BIT

    with progress_bar(formatters=custom_formatters, color_depth=color_depth) as pb:
        for i in pb(range(20), label='Downloading...'):
            time.sleep(1)


if __name__ == '__main__':
    main()
