#!/usr/bin/env python
"""
A simple chat application over telnet.
Everyone that connects is asked for his name, and then people can chat with
each other.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.eventloop import From, get_event_loop
from prompt_toolkit.layout.formatted_text import HTML
from prompt_toolkit.shortcuts import prompt_async, clear

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
    write = connection.send

    # When a client is connected, erase the screen from the client and say
    # Hello.
    clear()
    write('Welcome to our chat application!\n')
    write('All connected clients will receive what you say.\n')

    name = yield From(prompt_async(message='Type your name: '))

    # Random color.
    color = random.choice(COLORS)
    _connection_to_color[connection] = color

    # Send 'connected' message.
    _send_to_everyone(connection, name, '(connected)', color)

    # Prompt.
    prompt_msg = HTML('<reverse fg="{}">{}</reverse> ').format(color, name)

    _connections.append(connection)
    try:

        # Set CommandLineInterface.
        while True:
            result = yield From(prompt_async(message=prompt_msg))
            _send_to_everyone(connection, name, result, color)
    except KeyboardInterrupt:
        _send_to_everyone(connection, name, '(leaving)', color)
    finally:
        _connections.remove(connection)


def _send_to_everyone(sender_connection, name, message, color):
    """
    Send a message to all the clients.
    """
    for c in _connections:
        if c != sender_connection:
            c.send_above_prompt([
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
