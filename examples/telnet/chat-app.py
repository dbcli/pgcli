#!/usr/bin/env python
from __future__ import unicode_literals

from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.eventloop import From, get_event_loop
from prompt_toolkit.styles import ANSI_COLOR_NAMES

import logging
import random


# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

# List of connections.
_connections = []
_connection_to_color = {}


def interact(connection):
    # When a client is connected, erase the screen from the client and say
    # Hello.
    connection.erase_screen()
    connection.send('Welcome to our chat application!\n')
    connection.send('All connected clients will receive what you say.')

    name = yield From(connection.prompt_async(message='Type your name: '))

    # Random color.
    color = random.choice(ANSI_COLOR_NAMES)
    _connection_to_color[connection] = color

    # Prompt.
    prompt_msg = [('fg:' + color, ' [%s]> ' % name)]

    _connections.append(connection)
    try:

        # Set CommandLineInterface.
        while True:
            result = yield From(connection.prompt_async(message=prompt_msg))
            _send_to_everyone(name, result, color)
    finally:
        _connections.remove(connection)


def _send_to_everyone(name, message, color):
    for c in _connections:
        c.send_formatted_text([
            ('reverse fg:' + color, '[%s]' % name),
            ('', ' '),
            ('fg:' + color, message),
        ])


def main():
    server = TelnetServer(interact=interact, port=2323)
    server.start()
    get_event_loop().run_forever()


if __name__ == '__main__':
    main()
