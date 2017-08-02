#!/usr/bin/env python
"""
(Python >= 3.5)
This is an example of how to prompt inside an application that uses the asyncio
eventloop. The ``prompt_toolkit`` library will make sure that when other
coroutines are writing to stdout, they write above the prompt, not destroying
the input line.
This example does several things:
    1. It starts a simple coroutine, printing a counter to stdout every second.
    2. It starts a simple input/echo app loop which reads from stdin.
Very important is the following patch. If you are passing stdin by reference to
other parts of the code, make sure that this patch is applied as early as
possible. ::
    sys.stdout = app.stdout_proxy()
"""

from prompt_toolkit.shortcuts import Prompt
from prompt_toolkit.eventloop.defaults import create_asyncio_event_loop, set_event_loop
from prompt_toolkit.patch_stdout import patch_stdout

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
    set_event_loop(create_asyncio_event_loop())

    # Create Prompt.
    prompt = Prompt('Say something: ')

    # Patch stdout in something that will always print *above* the prompt when
    # something is written to stdout.
    # (This is optional, when `patch_stdout=True` has been given before.)

    ## sys.stdout = prompt.app.stdout_proxy()

    # Run echo loop. Read text from stdin, and reply it back.
    while True:
        try:
            result = await prompt.prompt(async_=True)
            print('You said: "{0}"'.format(result))
        except (EOFError, KeyboardInterrupt):
            return


def main():
    with patch_stdout():
        shell_task = asyncio.ensure_future(interactive_shell())
        background_task = asyncio.gather(print_counter(), return_exceptions=True)

        loop.run_until_complete(shell_task)
        background_task.cancel()
        loop.run_until_complete(background_task)
        print('Qutting event loop. Bye.')


if __name__ == '__main__':
    main()
