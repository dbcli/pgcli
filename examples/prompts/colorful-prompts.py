#!/usr/bin/env python
"""
Demonstration of a custom completer class and the possibility of styling
completions independently.
"""
from __future__ import unicode_literals
from prompt_toolkit.completion import Completion, Completer
from prompt_toolkit.shortcuts import prompt, CompleteStyle


colors = ['red', 'blue', 'green', 'orange', 'red', 'purple', 'yellow', 'cyan',
          'magenta', 'pink']


class ColorCompleter(Completer):
    def get_completions(self, document, complete_event):
        word = document.get_word_before_cursor()
        for color in colors:
            if color.startswith(word):
                yield Completion(
                    color,
                    start_position=-len(word),
                    style='fg:' + color,
                    selected_style='fg:white bg:' + color)


def main():
    # Simple completion menu.
    prompt('Color: ', completer=ColorCompleter())

    # Multi-column menu.
    prompt('Color: ', completer=ColorCompleter(),
           complete_style=CompleteStyle.MULTI_COLUMN)


if __name__ == '__main__':
    main()
