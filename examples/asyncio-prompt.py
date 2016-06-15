#!/usr/bin/env python
"""
(Python >= 3.5)
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

from prompt_toolkit.interface import CommandLineInterface
from prompt_toolkit.shortcuts import create_prompt_application, create_asyncio_eventloop, prompt_async

import asyncio
import sys

loop = asyncio.get_event_loop()


async def print_counter():
    """
    Coroutine that prints counters.
    """
    i = 0
    while True:
        print('Counter: %i' % i)
        i += 1
        await asyncio.sleep(3)


async def interactive_shell():
    """
    Like `interactive_shell`, but doing things manual.
    """
    # Create an asyncio `EventLoop` object. This is a wrapper around the
    # asyncio loop that can be passed into prompt_toolkit.
    eventloop = create_asyncio_eventloop()

    # Create interface.
    cli = CommandLineInterface(
        application=create_prompt_application('Say something inside the event loop: '),
        eventloop=eventloop)

    # Patch stdout in something that will always print *above* the prompt when
    # something is written to stdout.
    sys.stdout = cli.stdout_proxy()

    # Run echo loop. Read text from stdin, and reply it back.
    while True:
        try:
            result = await cli.run_async()
            print('You said: "{0}"'.format(result.text))
        except (EOFError, KeyboardInterrupt):
            return


def main():
    shell_task = loop.create_task(interactive_shell())

    # Gather all the async calls, so they can be cancelled at once
    background_task = asyncio.gather(print_counter(), return_exceptions=True)

    loop.run_until_complete(shell_task)
    background_task.cancel()
    loop.run_until_complete(background_task)
    print('Qutting event loop. Bye.')
    loop.close()


if __name__ == '__main__':
    main()
