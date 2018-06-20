"""
Win32 event loop.
"""
from __future__ import unicode_literals

from ..win32_types import SECURITY_ATTRIBUTES
from .base import EventLoop
from .context import wrap_in_current_context
from .future import Future
from .inputhook import InputHookContext
from .utils import ThreadWithFuture

from ctypes import windll, pointer
from ctypes.wintypes import DWORD, BOOL, HANDLE

import msvcrt

__all__ = [
    'Win32EventLoop',
    'wait_for_handles',
    'create_win32_event',
]

WAIT_TIMEOUT = 0x00000102
INFINITE = -1


class Win32EventLoop(EventLoop):
    """
    Event loop for Windows systems.

    :param recognize_paste: When True, try to discover paste actions and turn
        the event into a BracketedPaste.
    """
    def __init__(self, recognize_paste=True):
        super(Win32EventLoop, self).__init__()

        self._event = create_win32_event()
        self._calls_from_executor = []

        self.closed = False
        self._running = False

        # Additional readers.
        self._read_fds = {}  # Maps fd to handler.

        # Create inputhook context.
        self._inputhook_context = None

    def run_until_complete(self, future, inputhook=None):
        """
        Keep running the event loop until `future` has been set.

        :param future: :class:`prompt_toolkit.eventloop.future.Future` object.
        """
        assert isinstance(future, Future)
        assert inputhook is None or callable(inputhook)

        if self._running:
            raise Exception('Event loop is already running')
        if self.closed:
            raise Exception('Event loop already closed.')

        try:
            self._running = True

            while not future.done():
                self._run_once(inputhook)

            # Run one last time, to flush the pending `_calls_from_executor`s.
            if self._calls_from_executor:
                self._run_once(inputhook)

        finally:
            self._running = False

    def _run_once(self, inputhook):
        # Call inputhook.
        if inputhook:
            # Create input hook context.
            if self._inputhook_context is None:
                self._inputhook_context = InputHookContext()

            def ready(wait):
                " True when there is input ready. The inputhook should return control. "
                return bool(self._ready_for_reading(INFINITE if wait else 0))
            self._inputhook_context.call_inputhook(ready, inputhook)

        # Wait for the next event.
        handle = self._ready_for_reading(INFINITE)

        if handle == self._event:
            # When the Windows Event has been trigger, process the messages in the queue.
            windll.kernel32.ResetEvent(self._event)
            self._process_queued_calls_from_executor()

        elif handle in self._read_fds:
            callback = self._read_fds[handle]
            self._run_task(callback)

    def _run_task(self, t):
        try:
            t()
        except BaseException as e:
            self.call_exception_handler({
                'exception': e
            })

    def _ready_for_reading(self, timeout=INFINITE):
        """
        Return the handle that is ready for reading or `None` on timeout.
        """
        handles = [self._event]
        handles.extend(self._read_fds.keys())
        return wait_for_handles(handles, timeout)

    def close(self):
        self.closed = True

        # Clean up Event object.
        windll.kernel32.CloseHandle(self._event)

        if self._inputhook_context:
            self._inputhook_context.close()

    def run_in_executor(self, callback, _daemon=False):
        """
        Run a long running function in a background thread.
        (This is recommended for code that could block the event loop.)
        Similar to Twisted's ``deferToThread``.
        """
        th = ThreadWithFuture(callback, daemon=_daemon)

        # Wait until the main thread is idle for an instant before starting the
        # executor. (Like in eventloop/posix.py, we start the executor using
        # `call_from_executor`.)
        self.call_from_executor(th.start)
        return th.future

    def call_from_executor(self, callback, _max_postpone_until=None):
        """
        Call this function in the main event loop.
        Similar to Twisted's ``callFromThread``.
        """
        callback = wrap_in_current_context(callback)

        # Append to list of pending callbacks.
        self._calls_from_executor.append(callback)

        # Set Windows event.
        windll.kernel32.SetEvent(self._event)

    def _process_queued_calls_from_executor(self):
        # Process calls from executor.
        calls_from_executor = self._calls_from_executor[:]
        del self._calls_from_executor[:]

        for c in calls_from_executor:
            self._run_task(c)

    def add_reader(self, fd, callback):
        " Start watching the file descriptor for read availability. "
        callback = wrap_in_current_context(callback)

        h = msvcrt.get_osfhandle(fd)
        self.add_win32_handle(h, callback)

    def remove_reader(self, fd):
        " Stop watching the file descriptor for read availability. "
        h = msvcrt.get_osfhandle(fd)
        self.remove_win32_handle(h)

    def add_win32_handle(self, handle, callback):
        " Add a Win32 handle to the event loop. "
        callback = wrap_in_current_context(callback)
        self._read_fds[handle] = callback

    def remove_win32_handle(self, handle):
        " Remove a Win32 handle from the event loop. "
        if handle in self._read_fds:
            del self._read_fds[handle]


def wait_for_handles(handles, timeout=INFINITE):
    """
    Waits for multiple handles. (Similar to 'select') Returns the handle which is ready.
    Returns `None` on timeout.

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms687025(v=vs.85).aspx
    """
    assert isinstance(handles, list)
    assert isinstance(timeout, int)

    arrtype = HANDLE * len(handles)
    handle_array = arrtype(*handles)

    ret = windll.kernel32.WaitForMultipleObjects(
        len(handle_array), handle_array, BOOL(False), DWORD(timeout))

    if ret == WAIT_TIMEOUT:
        return None
    else:
        h = handle_array[ret]
        return h


def create_win32_event():
    """
    Creates a Win32 unnamed Event .

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms682396(v=vs.85).aspx
    """
    return windll.kernel32.CreateEventA(
        pointer(SECURITY_ATTRIBUTES()),
        BOOL(True),  # Manual reset event.
        BOOL(False),  # Initial state.
        None  # Unnamed event object.
    )
