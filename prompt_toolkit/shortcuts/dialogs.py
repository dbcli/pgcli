from __future__ import unicode_literals
import functools
from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.eventloop import run_in_executor
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import KeyBindings, merge_key_bindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.layout.dimension import Dimension as D
from prompt_toolkit.widgets import ProgressBar, Dialog, Button, Label, Box, TextArea, RadioList

__all__ = [
    'yes_no_dialog',
    'button_dialog',
    'input_dialog',
    'message_dialog',
    'radiolist_dialog',
    'progress_dialog',
]


def yes_no_dialog(title='', text='', yes_text='Yes', no_text='No', style=None,
                  async_=False):
    """
    Display a Yes/No dialog.
    Return a boolean.
    """
    def yes_handler():
        get_app().exit(result=True)

    def no_handler():
        get_app().exit(result=False)

    dialog = Dialog(
        title=title,
        body=Label(text=text, dont_extend_height=True),
        buttons=[
            Button(text=yes_text, handler=yes_handler),
            Button(text=no_text, handler=no_handler),
        ], with_background=True)

    return _run_dialog(dialog, style, async_=async_)


def button_dialog(title='', text='', buttons=[], style=None,
                  async_=False):
    """
    Display a dialog with button choices (given as a list of tuples).
    Return the value associated with button.
    """
    def button_handler(v):
        get_app().exit(result=v)

    dialog = Dialog(
        title=title,
        body=Label(text=text, dont_extend_height=True),
        buttons=[Button(text=t, handler=functools.partial(button_handler, v)) for t, v in buttons],
        with_background=True)

    return _run_dialog(dialog, style, async_=async_)


def input_dialog(title='', text='', ok_text='OK', cancel_text='Cancel',
                 completer=None, password=False, style=None, async_=False):
    """
    Display a text input box.
    Return the given text, or None when cancelled.
    """
    def accept(buf):
        get_app().layout.focus(ok_button)

    def ok_handler():
        get_app().exit(result=textfield.text)

    ok_button = Button(text=ok_text, handler=ok_handler)
    cancel_button = Button(text=cancel_text, handler=_return_none)

    textfield = TextArea(
        multiline=False,
        password=password,
        completer=completer,
        accept_handler=accept)

    dialog = Dialog(
        title=title,
        body=HSplit([
            Label(text=text, dont_extend_height=True),
            textfield,
        ], padding=D(preferred=1, max=1)),
        buttons=[ok_button, cancel_button],
        with_background=True)

    return _run_dialog(dialog, style, async_=async_)


def message_dialog(title='', text='', ok_text='Ok', style=None, async_=False):
    """
    Display a simple message box and wait until the user presses enter.
    """
    dialog = Dialog(
        title=title,
        body=Label(text=text, dont_extend_height=True),
        buttons=[
            Button(text=ok_text, handler=_return_none),
        ],
        with_background=True)

    return _run_dialog(dialog, style, async_=async_)


def radiolist_dialog(title='', text='', ok_text='Ok', cancel_text='Cancel',
                     values=None, style=None, async_=False):
    """
    Display a simple message box and wait until the user presses enter.
    """
    def ok_handler():
        get_app().exit(result=radio_list.current_value)

    radio_list = RadioList(values)

    dialog = Dialog(
        title=title,
        body=HSplit([
            Label(text=text, dont_extend_height=True),
            radio_list,
        ], padding=1),
        buttons=[
            Button(text=ok_text, handler=ok_handler),
            Button(text=cancel_text, handler=_return_none),
        ],
        with_background=True)

    return _run_dialog(dialog, style, async_=async_)


def progress_dialog(title='', text='', run_callback=None, style=None, async_=False):
    """
    :param run_callback: A function that receives as input a `set_percentage`
        function and it does the work.
    """
    assert callable(run_callback)

    progressbar = ProgressBar()
    text_area = TextArea(
        focusable=False,

        # Prefer this text area as big as possible, to avoid having a window
        # that keeps resizing when we add text to it.
        height=D(preferred=10**10))

    dialog = Dialog(
        body=HSplit([
            Box(Label(text=text)),
            Box(text_area, padding=D.exact(1)),
            progressbar,
        ]),
        title=title,
        with_background=True)
    app = _create_app(dialog, style)

    def set_percentage(value):
        progressbar.percentage = int(value)
        app.invalidate()

    def log_text(text):
        text_area.buffer.insert_text(text)
        app.invalidate()

    # Run the callback in the executor. When done, set a return value for the
    # UI, so that it quits.
    def start():
        try:
            run_callback(set_percentage, log_text)
        finally:
            app.exit()

    run_in_executor(start)

    if async_:
        return app.run_async()
    else:
        return app.run()


def _run_dialog(dialog, style, async_=False):
    " Turn the `Dialog` into an `Application` and run it. "
    application = _create_app(dialog, style)
    if async_:
        return application.run_async()
    else:
        return application.run()


def _create_app(dialog, style):
    # Key bindings.
    bindings = KeyBindings()
    bindings.add('tab')(focus_next)
    bindings.add('s-tab')(focus_previous)

    return Application(
        layout=Layout(dialog),
        key_bindings=merge_key_bindings([
            load_key_bindings(),
            bindings,
        ]),
        mouse_support=True,
        style=style,
        full_screen=True)


def _return_none():
    " Button handler that returns None. "
    get_app().exit()
