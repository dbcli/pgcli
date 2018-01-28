"""
Task local storage for coroutines.

Example::

    # Create a new task local.
    my_local = TaskLocal()

    # Set/retrieve/erase:
    my_local.set(value)

    value = my_local.get()

    my_local.delete()

A new scope can be created as follows::

    with context():
        ...

Within this scope, a new value can be assigned, which is only visible within
the scope. The scope as passed along when code is sent to an executor and back.
"""
from __future__ import unicode_literals
from threading import local
from functools import wraps

__all__ = [
    'context',
    'get_context_id',
    'wrap_in_current_context',
    'TaskLocal',
    'TaskLocalNotSetError',
]


_storage = local()
_last_context_id = 0


def get_context_id():
    " Return the current context ID or None. "
    try:
        return _storage.context_id
    except AttributeError:
        return 0  # Default context.


class context(object):
    """
    Context manager that activates a new scope.
    """
    def __init__(self, context_id=None):
        global _last_context_id

        if context_id is not None:
            self.id = context_id
        else:
            _last_context_id += 1
            self.id = _last_context_id

    def __enter__(self):
        try:
            self._previous_id = _storage.context_id
        except AttributeError:
            self._previous_id = None

        _storage.context_id = self.id
        return self.id

    def __exit__(self, *a):
        if self._previous_id is None:
            del _storage.context_id
        else:
            _storage.context_id = self._previous_id


class TaskLocal(object):
    """
    Like a thread local, but tied to the current task.
    """
    def __init__(self):
        self._storage = {}

    def get(self):
        try:
            ctx = get_context_id()
            return self._storage[ctx]
        except KeyError:
            raise TaskLocalNotSetError

    def set(self, value):
        ctx = get_context_id()
        self._storage[ctx] = value

    def delete(self):
        ctx = get_context_id()
        try:
            del self._storage[ctx]
        except KeyError:
            pass


def wrap_in_current_context(func):
    """
    Decorator that takes a function, and ensures that when it's called, the
    current context will apply.
    """
    assert callable(func)
    ctx_id = get_context_id()

    @wraps(func)
    def new_func(*a, **kw):
        with context(ctx_id):
            return func(*a, **kw)
    return new_func


class TaskLocalNotSetError(Exception):
    pass
