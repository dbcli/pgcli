#!/usr/bin/env python
"""
(Python >3.3)

This is an example of how to embed a CommandLineInterface inside an application
that uses the asyncio eventloop. The ``prompt_toolkit`` library will make sure
that when other coroutines are writing to stdout, they write above the prompt,
not destroying the input line.

This example does several things:
    1. It starts a simple coroutine, printing a counter to stdout every second.
    2. It starts a simple input/echo cli loop which reads from stdin.

Very important is the following patch. If you are passing stdin by reference to
other parts of the code, make sure that this patch is applied as early as
possible. ::

    sys.stdout = cli.stdout_proxy()
"""
from __future__ import unicode_literals
from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.shortcuts import create_default_application, create_asyncio_eventloop

import asyncio
import sys


loop = asyncio.get_event_loop()


@asyncio.coroutine
def print_counter():
    """
    Coroutine that prints counters.
    """
    i = 0
    while True:
        print('Counter: %i' % i)
        i += 1
        yield from asyncio.sleep(3)


@asyncio.coroutine
def interactive_shell():
    """
    Coroutine that shows the interactive command line.
    """
    # Create an asyncio `EventLoop` object. This is a wrapper around the
    # asyncio loop that can be passed into prompt_toolkit.
    eventloop = create_asyncio_eventloop()

    # Create interface.
    cli = CommandLineInterface(
        application=create_default_application('Say something inside the event loop: '),
        eventloop=eventloop)

    # Patch stdout in something that will always print *above* the prompt when
    # something is written to stdout.
    sys.stdout = cli.stdout_proxy()

    # Run echo loop. Read text from stdin, and reply it back.
    while True:
        try:
            result = yield from cli.run_async()
            print('You said: "%s"\n' % result.text)
        except (EOFError, KeyboardInterrupt):
            loop.stop()
            print('Qutting event loop. Bye.')
            return


def main():
    asyncio.async(print_counter())
    asyncio.async(interactive_shell())

    loop.run_forever()
    loop.close()


if __name__ == '__main__':
    main()
