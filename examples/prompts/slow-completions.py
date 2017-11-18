#!/usr/bin/env python
"""
An example of how to deal with slow auto completion code.

- Use `ThreadedCompleter` to make sure that the ``get_completions`` function is
  executed in a background thread.
- Set a `loading` boolean in the completer function to keep track of when the
  completer is running, and display this in the toolbar.
"""
from __future__ import unicode_literals

from prompt_toolkit.completion import ThreadedCompleter, Completer, Completion
from prompt_toolkit import prompt
import time

WORDS = [
    'alligator', 'ant', 'ape', 'bat', 'bear', 'beaver', 'bee', 'bison',
    'butterfly', 'cat', 'chicken', 'crocodile', 'dinosaur', 'dog', 'dolphine',
    'dove', 'duck', 'eagle', 'elephant', 'fish', 'goat', 'gorilla', 'kangaroo',
    'leopard', 'lion', 'mouse', 'rabbit', 'rat', 'snake', 'spider', 'turkey',
    'turtle',
]


class SlowCompleter(Completer):
    """
    This is a completer that's very slow.
    """
    def __init__(self):
        self.loading = False

    def get_completions(self, document, complete_event):
        self.loading = True
        word_before_cursor = document.get_word_before_cursor()

        time.sleep(.5)  # Simulate slowness.
        raise ''

        for word in WORDS:
            if word.startswith(word_before_cursor):
                yield Completion(word, -len(word_before_cursor))

        self.loading = False


def main():
    # We wrap it in a ThreadedCompleter, to make sure it runs in a different
    # thread. That way, we don't block the UI while running the completions.
    my_completer = SlowCompleter()
    threaded_completer = ThreadedCompleter(my_completer)

    # Add a bottom toolbar that display when completions are loading.
    def bottom_toolbar():
        return ' Loading completions... ' if my_completer.loading else ''

    # Display prompt.
    text = prompt('Give some animals: ', completer=threaded_completer,
                  complete_while_typing=True, bottom_toolbar=bottom_toolbar)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
