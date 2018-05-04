#!/usr/bin/env python
"""
An example of a prompt_toolkit coroutine and `Future` objects.
Probably you won't need this in your own applications, but it can be helpful
for understanding how the `prompt_toolkit` event loops works.

If you need asynchronous programming in your own application, it could be worth
considering to use asyncio instead. The reason that prompt_toolkit implements
its own event loop is because we still need to support Python 2, but it does
run on top of asyncio as well if needed.
"""
from prompt_toolkit.eventloop import From, Return, get_event_loop, ensure_future, Future
from prompt_toolkit.eventloop import run_in_executor
import time


#
# The following functions are all asynchronous functions that return a
# prompt_toolkit `Future` object.
#

def async_1():
    """
    Runs some code in an executor (other thread).
    """
    def in_executor():
        time.sleep(1)
        return 'Hello from async_1'
    return run_in_executor(in_executor)


def async_2():
    """
    Raise an exception in the executor.
    """
    def in_executor():
        time.sleep(.2)
        raise Exception('Failure from async_2')
    return run_in_executor(in_executor)


def async_3():
    " Succeed immediately. "
    return Future.succeed('Hello from async_3')


def async_4():
    " Fail immediately. "
    return Future.fail(Exception('Failure from async_4'))


def async_5():
    " Create a `Future` and call `set_result` later on. "
    f = Future()

    def in_executor():
        time.sleep(.2)
        f.set_result('Hello from async_5')

    run_in_executor(in_executor)
    return f


def async_6():
    " Create a `Future` and call `set_exception` later on. "
    f = Future()

    def in_executor():
        time.sleep(.2)
        f.set_exception(Exception('Failure from async_6'))

    run_in_executor(in_executor)
    return f


#
# Here we have the main coroutine that calls the previous asynchronous
# functions, each time waiting for the result before calling the next function.
# The coroutine needs to passed to `ensure_future` in order to run it in the
# event loop.
#


def my_coroutine():
    """
    A coroutine example. "yield-from" is used to wait for a `Future` or another
    coroutine.
    """
    # Wait for first future.
    value = yield From(async_1())
    print('async_1 returned: ', value)

    # Wait for second future.
    try:
        value = yield From(async_2())
    except Exception as e:
        print('async_2 raised: ', e)
    else:
        print('async_2 returned: ', value)

    # Wait for third future.
    value = yield From(async_3())
    print('async_3 returned: ', value)

    # Wait for fourth future.
    try:
        value = yield From(async_4())
    except Exception as e:
        print('async_4 raised: ', e)
    else:
        print('async_4 returned: ', value)

    # Wait for fifth future.
    value = yield From(async_5())
    print('async_5 returned: ', value)

    # Wait for sixth future.
    try:
        value = yield From(async_6())
    except Exception as e:
        print('async_6 raised: ', e)
    else:
        print('async_6 returned: ', value)

    # Wait for another coroutine.
    value = yield From(other_coroutine())
    print('other_coroutine returned: ', value)

    raise Return('result')


def other_coroutine():
    value = yield From(Future.succeed(True))
    value = yield From(Future.succeed(True))
    raise Return('Result from coroutine.')


def main():
    loop = get_event_loop()
    f = ensure_future(my_coroutine())

    # Run the event loop, until the coroutine is done.
    loop.run_until_complete(f)
    print(f.result())


if __name__ == '__main__':
    main()
