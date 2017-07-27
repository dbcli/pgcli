#!/usr/bin/env python
"""
A simple Telnet application that asks for input and responds.

The interaction function is an asyncio coroutine.
"""
from __future__ import unicode_literals

from prompt_toolkit.contrib.telnet.server import TelnetServer
from prompt_toolkit.eventloop.defaults import use_asyncio_event_loop

import logging
import asyncio

# Set up logging
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)

# Tell prompt_toolkit to use the asyncio event loop.
use_asyncio_event_loop()


async def interact(connection):
    connection.erase_screen()
    connection.send('Welcome!\n')

    # Ask for input.
    result = await connection.prompt_async(message='Say something: ')

    # Send output.
    connection.send('You said: {}\n'.format(result))
    connection.send('Bye.\n')


def main():
    server = TelnetServer(interact=interact, port=2323)
    server.start()
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
