#!/usr/bin/env python
"""
A simple Telnet application that asks for input and responds.

The interaction function is a prompt_toolkit coroutine.
Also see the `hello-world-asyncio.py` example which uses an asyncio coroutine.
That is probably the preferred way if you only need Python 3 support.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.eventloop import From, get_event_loop

import logging

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def interact(connection):
    connection.erase_screen()
    connection.send('Welcome!\n')

    # Ask for input.
    result = yield From(
        connection.prompt_async(message='Say something: '))

    # Send output.
    connection.send('You said: {}\n'.format(result))
    connection.send('Bye.\n')


def main():
    server = TelnetServer(interact=interact, port=2323)
    server.start()
    get_event_loop().run_forever()


if __name__ == '__main__':
    main()
