#!/usr/bin/env python
from __future__ import unicode_literals

from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.eventloop import From, get_event_loop

import logging
import random


# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

# List of connections.
_connections = []
_connection_to_color = {}

COLORS = [
    'ansired', 'ansigreen', 'ansiyellow', 'ansiblue', 'ansifuchsia',
    'ansiturquoise', 'ansilightgray', 'ansidarkgray', 'ansidarkred',
    'ansidarkgreen', 'ansibrown', 'ansidarkblue', 'ansipurple', 'ansiteal']

def interact(connection):
    # When a client is connected, erase the screen from the client and say
    # Hello.
    connection.erase_screen()
    connection.send('Welcome to our chat application!\n')
    connection.send('All connected clients will receive what you say.')

    name = yield From(connection.prompt_async(message='Type your name: '))

    # Random color.
    color = random.choice(COLORS)
    _connection_to_color[connection] = color

    # Send 'connected' message.
    _send_to_everyone(connection, name, '(connected)', color)

    # Prompt.
    prompt_msg = [
        ('reverse fg:' + color, '[%s]>' % name),
        ('', ' '),
    ]

    _connections.append(connection)
    try:

        # Set CommandLineInterface.
        while True:
            result = yield From(connection.prompt_async(message=prompt_msg))
            _send_to_everyone(connection, name, result, color)
    finally:
        _connections.remove(connection)


def _send_to_everyone(sender_connection, name, message, color):
    """
    Send a message to all the clients.
    """
    for c in _connections:
        if c != sender_connection:
            c.send_formatted_text([
                ('fg:' + color, '[%s]' % name),
                ('', ' '),
                ('fg:' + color, '%s\n' % message),
            ])


def main():
    server = TelnetServer(interact=interact, port=2323)
    server.start()
    get_event_loop().run_forever()


if __name__ == '__main__':
    main()
