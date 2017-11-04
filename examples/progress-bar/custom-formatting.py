"""
A very simple progress bar which keep track of the progress as we consume an
iterator.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts.progress_bar import progress_bar, Formatter
from prompt_toolkit.styles import Style
import time

style = Style.from_dict({
    'progressbar title': '#0000ff',
    'item-title': '#ff4400 underline',
    'percentage': '#00ff00',
    'bar-a': 'bg:#00ff00 #004400',
    'bar-b': 'bg:#00ff00 #000000',
    'bar-c': 'bg:#000000 #000000',
    'current': '#448844',
    'total': '#448844',
    'time-elapsed': '#444488',
    'eta': 'bg:#88ff88 #ffffff',
})


def main():
    formatter = Formatter(sym_a='#', sym_b='#', sym_c='.')
    with progress_bar(title='Progress bar example with custom formatter.', formatter=formatter) as pb:
        for i in pb(range(1600), title='Downloading...'):
            time.sleep(.01)


if __name__ == '__main__':
    main()
