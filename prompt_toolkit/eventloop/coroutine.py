from __future__ import unicode_literals
import types
from prompt_toolkit.eventloop.defaults import get_event_loop
from prompt_toolkit.eventloop.future import Future

__all__ = [
    'From',
    'Return',
    'ensure_future',
]


def ensure_future(future_or_coroutine):
    """
    Take a coroutine (generator) or a `Future` object, and make sure to return
    a `Future`.
    """
    if isinstance(future_or_coroutine, Future):
        return future_or_coroutine
    elif isinstance(future_or_coroutine, types.GeneratorType):
        return _run_coroutine(future_or_coroutine)
    else:
        raise ValueError('Expecting coroutine or Future object. Got %r: %r' % (
                         type(future_or_coroutine), future_or_coroutine))


class Return(Exception):
    """
    For backwards-compatibility with Python2: when "return" is not supported in
    a generator/coroutine.  (Like Trollius.)

    Instead of ``return value``, in a coroutine do:  ``raise Return(value)``.
    """
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return 'Return(%r)' % (self.value, )


def From(obj):
    """
    Used to emulate 'yield from'.
    (Like Trollius does.)
    """
    return ensure_future(obj)


def _run_coroutine(coroutine):
    """
    Takes a generator that can yield Future instances.

    Example:

        def gen():
            yield From(...)
            print('...')
            yield From(...)
        ensure_future(gen())

    The values which are yielded by the given coroutine are supposed to be
    `Future` objects.
    """
    assert isinstance(coroutine, types.GeneratorType)
    loop = get_event_loop()

    result_f = loop.create_future()

    # Wrap this future in a `_FutureRef`. We need this in order to be able to
    # break all its references when we're done. This is important
    # because in case of an exception, we want to be sure that
    # `result_f.__del__` is triggered as soon as possible, so that we see the
    # exception.

    # (If `step_next` had a direct reference to `result_f` and there is a
    # future that references `step_next`, then sometimes it won't be cleaned up
    # immediately. - I'm not sure how exactly, but in that case it requires the
    # garbage collector, because refcounting isn't sufficient.)
    ref = _FutureRef(result_f)

    # Loop through the generator.
    def step_next(f=None):
        " Execute next step of the coroutine."
        try:
            if f is None:
                new_f = coroutine.send(None)
            else:
                exc = f.exception()
                if exc:
                    new_f = coroutine.throw(exc)
                else:
                    new_f = coroutine.send(f.result())
        except StopIteration as e:
            # Stop coroutine. Make sure that a result has been set in the future,
            # this will call the callbacks. (Also, don't take any result from
            # StopIteration, it has already been set using `raise Return()`.
            if not ref.future.done():
                ref.future.set_result(None)
                ref.forget()
        except Return as e:
            ref.future.set_result(e.value)
            ref.forget()
        except BaseException as e:
            ref.future.set_exception(e)
            ref.forget()
        else:
            # Process yielded value from coroutine.
            assert isinstance(new_f, Future), 'got %r' % (new_f, )

            @new_f.add_done_callback
            def continue_(_):
                step_next(new_f)

    # Start processing coroutine.
    step_next()

    return result_f


class _FutureRef(object):
    def __init__(self, future):
        self.future = future

    def forget(self):
        " Forget reference. "
        self.future = None
