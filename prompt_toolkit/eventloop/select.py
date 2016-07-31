from __future__ import unicode_literals, absolute_import
import sys
import select
import errno

__all__ = (
    'select_fds',
)

def _fd_to_int(fd):
    if isinstance(fd, int):
        return fd
    else:
        return fd.fileno()


def select_fds(read_fds, timeout):
    """
    Wait for a list of file descriptors (`read_fds`) to become ready for
    reading. This chooses the most appropriate select-tool for use in
    prompt-toolkit.

    Note: This is an internal API that shouldn't be used for external projects.
    """
    # Map to ensure that we return the objects that were passed in originally.
    # Whether they are a fd integer or an object that has a fileno().
    # (The 'poll' implementation for instance, returns always integers.)
    fd_map = dict((_fd_to_int(fd), fd) for fd in read_fds)

    # Use of the 'select' module, that was introduced in Python3.4. We don't
    # use it before 3.5 however, because this is the point where this module
    # retries interrupted system calls.
    if sys.version_info >= (3, 5):
        try:
            result = _python3_selectors(read_fds, timeout)
        except PermissionError:
            # We had a situation (in pypager) where epoll raised a
            # PermissionError when a local file descriptor was registered,
            # however poll and select worked fine. So, in that case, just try
            # using select below.
            result = None
    else:
        result = None

    if result is None:
        try:
            # First, try the 'select' module. This is the most universal, and
            # powerful enough in our case.
            result = _select(read_fds, timeout)
        except ValueError:
            # When we have more than 1024 open file descriptors, we'll always
            # get a "ValueError: filedescriptor out of range in select()" for
            # 'select'. In this case, retry, using 'poll' instead.
            result = _poll(read_fds, timeout)

    return [fd_map[_fd_to_int(fd)] for fd in result]


def _python3_selectors(read_fds, timeout):
    """
    Use of the Python3 'selectors' module.

    NOTE: Only use on Python 3.5 or newer!
    """
    import selectors  # Inline import: Python3 only!
    sel = selectors.DefaultSelector()

    for fd in read_fds:
        sel.register(fd, selectors.EVENT_READ, None)

    events = sel.select(timeout=timeout)
    try:
        return [key.fileobj for key, mask in events]
    finally:
        sel.close()


def _poll(read_fds, timeout):
    """
    Use 'poll', to wait for any of the given `read_fds` to become ready.
    """
    p = select.poll()
    for fd in read_fds:
        p.register(fd, select.POLLIN)

    tuples = p.poll(timeout)  # Returns (fd, event) tuples.
    return [t[0] for t in tuples]


def _select(read_fds, timeout):
    """
    Wrapper around select.select.

    When the SIGWINCH signal is handled, other system calls, like select
    are aborted in Python. This wrapper will retry the system call.
    """
    while True:
        try:
            return select.select(read_fds, [], [], timeout)[0]
        except select.error as e:
            # Retry select call when EINTR
            if e.args and e.args[0] == errno.EINTR:
                continue
            else:
                raise
