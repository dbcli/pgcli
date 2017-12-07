#!/usr/bin/env python
"""
A simple progress bar, visualised with rainbow colors (for fun).
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.progress_bar import progress_bar, formatters
from prompt_toolkit.output.defaults import create_output
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

    output = create_output(true_color=true_color)

    with progress_bar(formatters=custom_formatters, output=output) as pb:
        for i in pb(range(20), label='Downloading...'):
            time.sleep(1)


if __name__ == '__main__':
    main()
