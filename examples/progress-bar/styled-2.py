#!/usr/bin/env python
"""
A very simple progress bar which keep track of the progress as we consume an
iterator.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.progress_bar import progress_bar
from prompt_toolkit.styles import Style
from prompt_toolkit.shortcuts.progress_bar import formatters
from prompt_toolkit.formatted_text import HTML
import time


style = Style.from_dict({
    'progressbar title': '#0000ff',
    'item-title': '#ff4400 underline',
    'percentage': '#00ff00',
    'bar-a': 'bg:#00ff00 #004400',
    'bar-b': 'bg:#00ff00 #000000',
    'bar-c': 'bg:#000000 #000000',
    'tildes': '#444488',
    'time-left': 'bg:#88ff88 #ffffff',
    'spinning-wheel': 'bg:#ffff00 #000000',
})


def main():
    custom_formatters = [
        formatters.Label(),
        formatters.Text(' '),
        formatters.SpinningWheel(),
        formatters.Text(' '),
        formatters.Text(HTML('<tildes>~~~</tildes>')),
        formatters.Bar(sym_a='#', sym_b='#', sym_c='.'),
        formatters.Text(' left: '),
        formatters.TimeLeft(),
    ]
    with progress_bar(title='Progress bar example with custom formatter.', formatters=custom_formatters, style=style) as pb:
        for i in pb(range(20), label='Downloading...'):
            time.sleep(1)


if __name__ == '__main__':
    main()
