"""
Implementation for async generators.

An asynchronous generator is one that can both produce `Future` objects as well
as actual values. These values have to be wrapped in a `AsyncGeneratorItem` in
order to be recognized. In the future, we can use the asynchronous generators
from Python 3 (and asyncio).

.. code:: python

    def async_generator():
        yield From(...)
        yield AsyncGeneratorItem(some_value)
        yield From(...)
        yield AsyncGeneratorItem(some_value)
        ...
"""
from __future__ import unicode_literals
from six.moves.queue import Queue
from threading import RLock
from .defaults import run_in_executor
from .future import Future
from .coroutine import From, Return

__all__ = [
    'AsyncGeneratorItem',
    'generator_to_async_generator',
    'consume_async_generator',
]


class AsyncGeneratorItem(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return 'AsyncGeneratorItem(%r)' % (self.value, )


def generator_to_async_generator(get_iterable):
    """
    Turn a generator or iterable into an async generator.

    This works by running the generator in a background thread.
    The new async generator will yield both `Future` objects as well
    as the original items.

    :param get_iterable: Function that returns a generator or iterable when
        called.
    """
    q = Queue()
    f = Future()
    l = RLock()
    quitting = False

    def runner():
        """
        Consume the generator in background thread.
        When items are received, they'll be pushed to the queue and the
        Future is set.
        """
        for item in get_iterable():
            with l:
                q.put(item)
                if not f.done():
                    f.set_result(None)

            # When this async generator was cancelled (closed), stop this
            # thread.
            if quitting:
                break
        with l:
            if not f.done():
                f.set_result(None)

    # Start background thread.
    done_f = run_in_executor(runner, _daemon=True)

    try:
        while not done_f.done():
            # Wait for next item(s): yield Future.
            yield From(f)

            # Items received. Yield all items so far.
            with l:
                while not q.empty():
                    yield AsyncGeneratorItem(q.get())

                f = Future()

        # Yield final items.
        while not q.empty():
            yield q.get()

    finally:
        # When this async generator is closed (GeneratorExit exception, stop
        # the background thread as well. - we don't need that anymore.)
        quitting = True


def consume_async_generator(iterator, cancel, item_callback):
    """
    Consume an asynchronous generator.

    :param cancel: Cancel the consumption of the generator when this callable
        return True.
    :param item_callback: This will be called for each item that we receive.
    """
    assert callable(cancel)
    assert callable(item_callback)

    send = None
    try:
        item = iterator.send(send)
    except StopIteration:
        return

    while True:
        if cancel():
            break

        if isinstance(item, AsyncGeneratorItem):
            # Got item.
            item_callback(item.value)
            send = None

        elif isinstance(item, Future):
            # Process future.
            try:
                send = yield From(item)
            except BaseException as e:
                try:
                    item = iterator.throw(e)
                except StopIteration:
                    break
        else:
            raise TypeError('Expecting Completion or Future, got %r' % (item, ))

        try:
            item = iterator.send(send)
        except StopIteration:
            break

    raise Return(None)
