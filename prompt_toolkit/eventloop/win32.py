from __future__ import unicode_literals

from ..terminal.win32_input import ConsoleInputReader
from ..win32_types import SECURITY_ATTRIBUTES
from .base import BaseEventLoop

from ctypes import windll, pointer, c_long
from ctypes.wintypes import DWORD, BOOL


__all__ = (
    'Win32EventLoop',
)

WAIT_TIMEOUT = 0x00000102


class Win32EventLoop(BaseEventLoop):
    def __init__(self, input_processor, stdin):
        super(Win32EventLoop, self).__init__(input_processor, stdin)
        self._event = _create_event()
        self._console_input_reader = ConsoleInputReader()
        self._calls_from_executor = []

        # XXX: There is still one bug here. When input has been read from the
        #      ConsoleInputReader, `_wait_for_handles` never returns the Event
        #      as signalled anymore.

    def loop(self):
        if self.closed:
            raise Exception('Event loop already closed.')

        timeout = int(1000 * self.input_timeout)

        while True:
            handle = _wait_for_handles([self._event, self._console_input_reader.handle], timeout)

            if handle == self._event:
                windll.kernel32.ResetEvent(self._event)
                self._process_queued_calls_from_executor()
                return

            elif handle == self._console_input_reader.handle:
                keys = self._console_input_reader.read()
                for k in keys:
                    self.input_processor.feed_key(k)
                return

            else:
                # Fire input timeout event.
                self.onInputTimeout.fire()
                timeout = -1

    def close(self):
        super(Win32EventLoop, self).close()

        # Clean up Event object.
        windll.kernel32.CloseHandle(self._event)

    def call_from_executor(self, callback):
        """
        Call this function in the main event loop.
        Similar to Twisted's ``callFromThread``.
        """
        # Append to list of pending callbacks.
        self._calls_from_executor.append(callback)

        # Set Windows event.
        windll.kernel32.SetEvent(self._event)

    def _process_queued_calls_from_executor(self):
        # Process calls from executor.
        calls_from_executor, self._calls_from_executor = self._calls_from_executor, []
        for c in calls_from_executor:
            c()


def _wait_for_handles(handles, timeout=-1):
    """
    Waits for multiple handles. (Similar to 'select') Returns the handle which is ready.

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms687025(v=vs.85).aspx
    """
    arrtype = c_long * len(handles)
    handle_array = arrtype(*handles)
    ret = windll.kernel32.WaitForMultipleObjects(len(handle_array), handle_array, False, DWORD(timeout))

    if ret == WAIT_TIMEOUT:
        return None
    else:
        h = handle_array[ret]
        return h


def _create_event():
    """
    Creates a Win32 unnamed Event .

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms682396(v=vs.85).aspx
    """
    return windll.kernel32.CreateEventA(pointer(SECURITY_ATTRIBUTES()), BOOL(True), BOOL(False), None)
