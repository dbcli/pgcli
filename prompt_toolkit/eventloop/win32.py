"""
Win32 asyncio event loop.

Windows notes:
    - Somehow it doesn't seem to work with the 'ProactorEventLoop'.
"""
from __future__ import unicode_literals

from ..terminal.win32_input import ConsoleInputReader
from ..win32_types import SECURITY_ATTRIBUTES
from .base import EventLoop, INPUT_TIMEOUT
from .inputhook import InputHookContext
from .utils import TimeIt

from ctypes import windll, pointer
from ctypes.wintypes import DWORD, BOOL, HANDLE

import threading

__all__ = (
    'Win32EventLoop',
)

WAIT_TIMEOUT = 0x00000102
INPUT_TIMEOUT_MS = int(1000 * INPUT_TIMEOUT)


class Win32EventLoop(EventLoop):
    def __init__(self, inputhook=None):
        assert inputhook is None or callable(inputhook)

        self._event = _create_event()
        self._console_input_reader = ConsoleInputReader()
        self._calls_from_executor = []

        self.closed = False
        self._running = False

        # Create inputhook context.
        self._inputhook_context = InputHookContext(inputhook) if inputhook else None

    def run(self, stdin, callbacks):
        if self.closed:
            raise Exception('Event loop already closed.')

        current_timeout = INPUT_TIMEOUT_MS
        self._running = True

        while self._running:
            # Call inputhook.
            with TimeIt() as inputhook_timer:
                if self._inputhook_context:
                    def ready(wait):
                        " True when there is input ready. The inputhook should return control. "
                        return bool(self._ready_for_reading(current_timeout if wait else 0))
                    self._inputhook_context.call_inputhook(ready)

            # Calculate remaining timeout. (The inputhook consumed some of the time.)
            if current_timeout == -1:
                remaining_timeout = -1
            else:
                remaining_timeout = max(0, current_timeout - int(1000 * inputhook_timer.duration))

            # Wait for the next event.
            handle = self._ready_for_reading(remaining_timeout)

            if handle == self._console_input_reader.handle:
                # When stdin is ready, read input and reset timeout timer.
                keys = self._console_input_reader.read()
                for k in keys:
                    callbacks.feed_key(k)
                callbacks.redraw()
                current_timeout = INPUT_TIMEOUT_MS

            elif handle == self._event:
                # When the Windows Event has been trigger, process the messages in the queue.
                windll.kernel32.ResetEvent(self._event)
                self._process_queued_calls_from_executor()

            else:
                # Fire input timeout event.
                callbacks.input_timeout()
                current_timeout = -1

    def _ready_for_reading(self, timeout=None):
        """
        Return the handle that is ready for reading or `None` on timeout.
        """
        return _wait_for_handles([self._event, self._console_input_reader.handle],
                                   timeout)

    def stop(self):
        self._running = False

    def close(self):
        self.closed = True

        # Clean up Event object.
        windll.kernel32.CloseHandle(self._event)

        if self._inputhook_context:
            self._inputhook_context.close()

    def run_in_executor(self, callback):
        """
        Run a long running function in a background thread.
        (This is recommended for code that could block the event loop.)
        Similar to Twisted's ``deferToThread``.
        """
        # Wait until the main thread is idle for an instant before starting the
        # executor. (Like in eventloop/posix.py, we start the executor using
        # `call_from_executor`.)
        def start_executor():
            threading.Thread(target=callback).start()
        self.call_from_executor(start_executor)

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
    Returns `None` on timeout.

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms687025(v=vs.85).aspx
    """
    arrtype = HANDLE * len(handles)
    handle_array = arrtype(*handles)

    ret = windll.kernel32.WaitForMultipleObjects(
        len(handle_array), handle_array, BOOL(False), DWORD(timeout))

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
