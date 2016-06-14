#!/usr/bin/env python
"""
Autocompletion example that displays the autocompletions like readline does by
binding a custom handler to the Tab key.
"""
from __future__ import unicode_literals

from prompt_toolkit import prompt
from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.key_binding.bindings.completion import display_completions_like_readline
from prompt_toolkit.key_binding.manager import KeyBindingManager
from prompt_toolkit.keys import Keys


animal_completer = WordCompleter([
    'alligator', 'ant', 'ape', 'bat', 'bear', 'beaver', 'bee', 'bison',
    'butterfly', 'cat', 'chicken', 'crocodile', 'dinosaur', 'dog', 'dolphine',
    'dove', 'duck', 'eagle', 'elephant', 'fish', 'goat', 'gorilla', 'kangoroo',
    'leopard', 'lion', 'mouse', 'rabbit', 'rat', 'snake', 'spider', 'turkey',
    'turtle',
], ignore_case=True)

# Create key bindings registry with a custom binding for the Tab key that
# displays completions like GNU readline.
key_bindings_manager = KeyBindingManager.for_prompt()
key_bindings_manager.registry.add_binding(Keys.ControlI)(display_completions_like_readline)

def main():
    text = prompt('Give some animals: ', completer=animal_completer,
                  key_bindings_registry=key_bindings_manager.registry,

                  # Important: for this to work: `complete_while_typing` needs
                  #            to be False.
                  complete_while_typing=False)
    print('You said: %s' % text)


if __name__ == '__main__':
    main()
