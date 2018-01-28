"""
Tools for running functions on the terminal above the current application or prompt.
"""
from __future__ import unicode_literals
from prompt_toolkit.eventloop import get_event_loop, ensure_future, Return, run_in_executor, From, Future
from .current import get_app

__all__ = [
    'run_in_terminal',
    'run_coroutine_in_terminal',
]


def run_in_terminal(func, render_cli_done=False, in_executor=False):
    """
    Run function on the terminal above the current application or prompt.

    What this does is first hiding the prompt, then running this callable
    (which can safely output to the terminal), and then again rendering the
    prompt which causes the output of this function to scroll above the
    prompt.

    :param func: The callable to execute.
    :param render_cli_done: When True, render the interface in the
            'Done' state first, then execute the function. If False,
            erase the interface first.
    :param in_executor: When True, run in executor. (Use this for long
        blocking functions, when you don't want to block the event loop.)

    :returns: A `Future`.
    """
    if in_executor:
        def async_func():
            f = run_in_executor(func)
            return f
    else:
        def async_func():
            result = func()
            return Future.succeed(result)

    return run_coroutine_in_terminal(async_func, render_cli_done=render_cli_done)


def run_coroutine_in_terminal(async_func, render_cli_done=False):
    """
    Suspend the current application and run this coroutine instead.
    `async_func` can be a coroutine or a function that returns a Future.

    :param async_func: A function that returns either a Future or coroutine
        when called.
    :returns: A `Future`.
    """
    assert callable(async_func)
    loop = get_event_loop()

    # Make sure to run this function in the current `Application`, or if no
    # application is active, run it normally.
    app = get_app(return_none=True)

    if app is None:
        return ensure_future(async_func())
    assert app._is_running

    # When a previous `run_in_terminal` call was in progress. Wait for that
    # to finish, before starting this one. Chain to previous call.
    previous_run_in_terminal_f = app._running_in_terminal_f
    new_run_in_terminal_f = loop.create_future()
    app._running_in_terminal_f = new_run_in_terminal_f

    def _run_in_t():
        " Coroutine. "
        # Wait for the previous `run_in_terminal` to finish.
        if previous_run_in_terminal_f is not None:
            yield previous_run_in_terminal_f

        # Draw interface in 'done' state, or erase.
        if render_cli_done:
            app._redraw(render_as_done=True)
        else:
            app.renderer.erase()

        # Disable rendering.
        app._running_in_terminal = True

        # Detach input.
        try:
            with app.input.detach():
                with app.input.cooked_mode():
                    result = yield From(async_func())

            raise Return(result)  # Same as: "return result"
        finally:
            # Redraw interface again.
            try:
                app._running_in_terminal = False
                app.renderer.reset()
                app._request_absolute_cursor_position()
                app._redraw()
            finally:
                new_run_in_terminal_f.set_result(None)

    return ensure_future(_run_in_t())
