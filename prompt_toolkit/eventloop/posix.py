from __future__ import unicode_literals
import fcntl
import os
import signal
import threading
import time

from prompt_toolkit.input import Input
from .base import EventLoop
from .future import Future
from .inputhook import InputHookContext
from .select import AutoSelector, Selector, fd_to_int

__all__ = (
    'PosixEventLoop',
)

_now = time.time


class PosixEventLoop(EventLoop):
    """
    Event loop for posix systems (Linux, Mac os X).
    """
    def __init__(self, inputhook=None, selector=AutoSelector):
        assert inputhook is None or callable(inputhook)
        assert issubclass(selector, Selector)

        self.closed = False
        self._running = False

        # The `Input` object that's currently attached.
        self._input = None
        self._input_ready_cb = None

        self._calls_from_executor = []
        self._read_fds = {}  # Maps fd to handler.
        self.selector = selector()

        self._signal_handler_mappings = {}  # signal: previous_handler

        # Create a pipe for inter thread communication.
        self._schedule_pipe = os.pipe()
        fcntl.fcntl(self._schedule_pipe[0], fcntl.F_SETFL, os.O_NONBLOCK)
        self.add_reader(self._schedule_pipe[0], None)

        # Create inputhook context.
        self._inputhook_context = InputHookContext(inputhook) if inputhook else None

    def run_until_complete(self, future):
        """
        Keep running the event loop until `future` has been set.

        :param future: :class:`prompt_toolkit.eventloop.future.Future` object.
        """
        assert isinstance(future, Future)
        assert not self._running
        if self.closed:
            raise Exception('Event loop already closed.')

        try:
            self._running = True

            while not future.done():
                self._run_once()

            # Run one last time, to flush the pending `_calls_from_executor`s.
            if self._calls_from_executor:
                self._run_once()

        finally:
            self._running = False

    def _run_once(self):
        # Call inputhook.
        if self._inputhook_context:
            def ready(wait):
                " True when there is input ready. The inputhook should return control. "
                return self._ready_for_reading(None if wait else 0) != []
            self._inputhook_context.call_inputhook(ready)

        # Wait until input is ready.
        fds = self._ready_for_reading(None)

        # When any of the FDs are ready. Call the appropriate callback.
        if fds:
            # Create lists of high/low priority tasks. The main reason for this
            # is to allow painting the UI to happen as soon as possible, but
            # when there are many events happening, we don't want to call the
            # UI renderer 1000x per second. If the eventloop is completely
            # saturated with many CPU intensive tasks (like processing
            # input/output), we say that drawing the UI can be postponed a
            # little, to make CPU available. This will be a low priority task
            # in that case.
            tasks = []
            low_priority_tasks = []
            now = None  # Lazy load time. (Fewer system calls.)

            for fd in fds:
                # For the 'call_from_executor' fd, put each pending
                # item on either the high or low priority queue.
                if fd == self._schedule_pipe[0]:
                    for c, max_postpone_until in self._calls_from_executor:
                        if max_postpone_until is None:
                            # Execute now.
                            tasks.append(c)
                        else:
                            # Execute soon, if `max_postpone_until` is in the future.
                            now = now or _now()
                            if max_postpone_until < now:
                                tasks.append(c)
                            else:
                                low_priority_tasks.append((c, max_postpone_until))
                    self._calls_from_executor = []

                    # Flush all the pipe content.
                    os.read(self._schedule_pipe[0], 1024)
                else:
                    handler = self._read_fds.get(fd)
                    if handler:
                        tasks.append(handler)

            # When there are high priority tasks, run all these.
            # Schedule low priority tasks for the next iteration.
            if tasks:
                for t in tasks:
                    t()

                # Postpone low priority tasks.
                for t, max_postpone_until in low_priority_tasks:
                    self.call_from_executor(t, _max_postpone_until=max_postpone_until)
            else:
                # Currently there are only low priority tasks -> run them right now.
                for t, _ in low_priority_tasks:
                    t()

    def _ready_for_reading(self, timeout=None):
        """
        Return the file descriptors that are ready for reading.
        """
        fds = self.selector.select(timeout)
        return fds

    def set_input(self, input, input_ready_callback):
        """
        Tell the eventloop to read from this input object.

        :param input: :class:`~prompt_toolkit.input.Input` object.
        :param input_ready_callback: Called when the input is ready to read.
        """
        assert isinstance(input, Input)
        assert callable(input_ready_callback)

        # Remove previous
        if self._input:
            previous_input = self._input
            previous_cb = self._input_ready_cb
            self.remove_input()
        else:
            previous_input = None
            previous_cb = None

        # Set current.
        self._input = input
        self._input_ready_cb = input_ready_callback

        # Add reader.
        def ready():
            input_ready_callback()

        self.add_reader(input.stdin.fileno(), ready)

        return previous_input, previous_cb

    def remove_input(self):
        """
        Remove the currently attached `Input`.
        """
        if self._input:
            previous_input = self._input
            previous_cb = self._input_ready_cb

            self.remove_reader(previous_input.fileno())
            self._input = None
            self._input_ready_cb = None

            return previous_input, previous_cb
        else:
            return None, None

    def add_signal_handler(self, signum, handler):
        """
        Register a signal handler. Call `handler` when `signal` was received.
        The given handler will always be called in the same thread as the
        eventloop. (Like `call_from_executor`.)
        """
        # Always process signals asynchronously, because these handlers can
        # write to the output, and doing this inside the signal handler causes
        # easily reentrant calls, giving runtime errors.

        # Furthur, this has to be thread safe. When the Application runs not in
        # the main thread, this function will still be called from the main
        # thread. (The only place where we can install signal handlers.)

        if handler is None:
            # Normally, `signal.signal` should never return `None`. For some
            # reason it happens here:
            # https://github.com/jonathanslenders/python-prompt-toolkit/pull/174
            handler = 0

        if handler in (signal.SIG_IGN, 0):
            # Clear handler.
            previous = signal.signal(signum, handler)
            self._signal_handler_mappings[signum] = handler
        else:
            # Set handler.
            def call_signal_handler(*a):
                self.call_from_executor(handler)

            previous = signal.signal(signum, call_signal_handler)
            self._signal_handler_mappings[signum] = handler

        # Return the previous signal handler.
        return self._signal_handler_mappings.get(signum, previous)

    def run_in_executor(self, callback, _daemon=False):
        """
        Run a long running function in a background thread.
        (This is recommended for code that could block the event loop.)
        Similar to Twisted's ``deferToThread``.
        """
        f = Future()

        # Wait until the main thread is idle.
        # We start the thread by using `call_from_executor`. The event loop
        # favours processing input over `calls_from_executor`, so the thread
        # will not start until there is no more input to process and the main
        # thread becomes idle for an instant. This is good, because Python
        # threading favours CPU over I/O -- an autocompletion thread in the
        # background would cause a significantly slow down of the main thread.
        # It is mostly noticable when pasting large portions of text while
        # having real time autocompletion while typing on.
        def run():
            try:
                result = callback()
            except BaseException as e:
                f.set_exception(e)
            else:
                f.set_result(result)

        def start_executor():
            t = threading.Thread(target=run)
            if _daemon:
                t.daemon = True
            t.start()
        self.call_from_executor(start_executor)

        return f

    def call_from_executor(self, callback, _max_postpone_until=None):
        """
        Call this function in the main event loop.
        Similar to Twisted's ``callFromThread``.

        :param _max_postpone_until: `None` or `time.time` value. For interal
            use. If the eventloop is saturated, consider this task to be low
            priority and postpone maximum until this timestamp. (For instance,
            repaint is done using low priority.)
        """
        assert _max_postpone_until is None or isinstance(_max_postpone_until, float)

        self._calls_from_executor.append((callback, _max_postpone_until))

        if self._schedule_pipe:
            try:
                os.write(self._schedule_pipe[1], b'x')
            except (AttributeError, IndexError, OSError):
                # Handle race condition. We're in a different thread.
                # - `_schedule_pipe` could have become None in the meantime.
                # - We catch `OSError` (actually BrokenPipeError), because the
                #   main thread could have closed the pipe already.
                pass

    def close(self):
        """
        Close the event loop. The loop must not be running.
        """
        assert not self._running
        self.closed = True

        # Close pipes.
        schedule_pipe = self._schedule_pipe
        self._schedule_pipe = None

        if schedule_pipe:
            os.close(schedule_pipe[0])
            os.close(schedule_pipe[1])

        if self._inputhook_context:
            self._inputhook_context.close()

    def add_reader(self, fd, callback):
        " Add read file descriptor to the event loop. "
        fd = fd_to_int(fd)
        self._read_fds[fd] = callback
        self.selector.register(fd)

    def remove_reader(self, fd):
        " Remove read file descriptor from the event loop. "
        fd = fd_to_int(fd)

        if fd in self._read_fds:
            del self._read_fds[fd]

        self.selector.unregister(fd)
