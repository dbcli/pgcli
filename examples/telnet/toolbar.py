#!/usr/bin/env python
"""
Example of a telnet application that displays a bottom toolbar and completions
in the prompt.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.completers import WordCompleter
from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.eventloop import From, get_event_loop
from prompt_toolkit.shortcuts import prompt_async

import logging

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def interact(connection):
    # When a client is connected, erase the screen from the client and say
    # Hello.
    connection.erase_screen()
    connection.send('Welcome!\n')

    # Display prompt with bottom toolbar.
    animal_completer = WordCompleter(['alligator', 'ant'])

    def get_toolbar():
        return 'Bottom toolbar...'

    result = yield From(prompt_async(
        'Say something: ',
        bottom_toolbar=get_toolbar,
        completer=animal_completer))

    connection.send('You said: {}\n'.format(result))
    connection.send('Bye.\n')


def main():
    server = TelnetServer(interact=interact, port=2323)
    server.start()
    get_event_loop().run_forever()


if __name__ == '__main__':
    main()
