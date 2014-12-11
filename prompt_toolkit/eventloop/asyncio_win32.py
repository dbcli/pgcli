"""
Win32 asyncio event loop.

Windows notes:
- Somehow it doesn't seem to work with the 'ProactorEventLoop'.
"""
from __future__ import unicode_literals

from .asyncio_base import BaseAsyncioEventLoop
from ..terminal.win32_input import ConsoleInputReader

import asyncio

__all__ = (
    'Win32AsyncioEventLoop',
)


class Win32AsyncioEventLoop(BaseAsyncioEventLoop):
    def __init__(self, input_processor, stdin, loop=None):
        super(Win32AsyncioEventLoop, self).__init__(input_processor, stdin)

        self._console_input_reader = ConsoleInputReader()

    def wait_for_input(self, f_ready):
        def wait():
            # Note: We cannot use "yield from", because this package also
            #       installs on Python 2.

            # Get keys
            try:
                for f in self.loop.run_in_executor(None, self._console_input_reader.read):
                    yield f
            except StopIteration as e:
                keys = e.args[0]

            # Feed keys to input processor.
            for k in keys:
                self.input_processor.feed_key(k)

            f_ready.set_result(None)
        asyncio.async(wait(), loop=self.loop)
