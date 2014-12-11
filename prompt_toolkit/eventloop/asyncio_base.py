"""
Eventloop for integration with Python3 asyncio.

Windows notes:
- Somehow it doesn't seem to work with the 'ProactorEventLoop'.

Note that we can't use "yield from", because the package should be installable
under Python 2.6 as well, and it should contain syntactically valid Python 2.6
code.
"""
from __future__ import unicode_literals

from codecs import getincrementaldecoder

from .base import BaseEventLoop

import asyncio

__all__ = (
    'BaseAsyncioEventLoop',
)


class BaseAsyncioEventLoop(BaseEventLoop):
    stdin_decoder_cls = getincrementaldecoder('utf-8')

    def __init__(self, input_processor, stdin, loop=None):
        super(BaseAsyncioEventLoop, self).__init__(input_processor, stdin)

        self.loop = loop or asyncio.get_event_loop()

    def wait_for_input(self, f_ready):
        raise NotImplementedError('')

    @asyncio.coroutine
    def loop_coroutine(self):
        """
        The input 'event loop'.
        """
        if self.closed:
            raise Exception('Event loop already closed.')

        f_ready = asyncio.Future()
        self.wait_for_input(f_ready)

        # Start a timeout coroutine.
        @asyncio.coroutine
        def timeout():
            for f in asyncio.sleep(self.input_timeout, loop=self.loop):
                yield f

            # Only fire timeout event when no input data was returned yet.
            if not f_ready.done():
                self.onInputTimeout.fire()
        asyncio.async(timeout(), loop=self.loop)

        # Return when there is input ready.
        for f in f_ready:
            yield f

    def run_in_executor(self, callback):
        self.loop.run_in_executor(None, callback)

    def call_from_executor(self, callback):
        """
        Call this function in the main event loop.
        Similar to Twisted's ``callFromThread``.
        """
        self.loop.call_soon(callback)
