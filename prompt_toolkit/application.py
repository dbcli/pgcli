from __future__ import unicode_literals

from .buffer import Buffer, AcceptAction
from .clipboard import Clipboard
from .filters import CLIFilter, Never
from .key_binding.bindings.basic import load_basic_bindings
from .key_binding.bindings.emacs import load_emacs_bindings
from .key_binding.registry import Registry
from .layout import Window
from .layout.controls import BufferControl
from .styles import DefaultStyle
from .utils import Callback
from .enums import DEFAULT_BUFFER
from .layout.containers import Layout

__all__ = (
    'AbortAction',
    'Application',
)


class AbortAction:
    """
    Actions to take on an Exit or Abort exception.
    """
    IGNORE = 'ignore'
    RETRY = 'retry'
    RAISE_EXCEPTION = 'raise-exception'
    RETURN_NONE = 'return-none'

    _all = (IGNORE, RETRY, RAISE_EXCEPTION, RETURN_NONE)


class Application(object):
    """
    Application class to be passed to a `CommandLineInterface`.

    This contains all customizable logic that is not I/O dependent.
    (So, what is independent of event loops, input and output.)

    This way, such an `Application` can run easily on several
    `CommandLineInterface`s, each with a different I/O backends.
    that runs for instance over telnet, SSH or any other I/O backend.

    :param layout: A :class:`Layout` instance.
    :param buffer: A :class:`Buffer` instance for the default buffer.
    :param initial_focussed_buffer: Name of the buffer that is focussed during start-up.
    :param key_bindings_registry: :class:`Registry` instance for the key bindings.
    :param clipboard: Clipboard to use.
    :param on_abort: What to do when Control-C is pressed.
    :param on_exit: What to do when Control-D is pressed.
    :param use_alternate_screen: When True, run the application on the alternate screen buffer.

    Filters:

    :param paste_mode: Filter.
    :param ignore_case: Filter.

    Callbacks:

    :param on_input_timeout: Called when there is no input for x seconds.
                    (Fired when any eventloop.onInputTimeout is fired.)
    :param on_start: Called when reading input starts.
    :param on_stop: Called when reading input ends.
    :param on_reset: Called during reset.
    :param on_buffer_changed: Called when another buffer gets the focus.
    :param on_initialize: Called after the `CommandLineInterface` initializes.
    """
    def __init__(self, layout=None, buffer=None, buffers=None,
                 initial_focussed_buffer=DEFAULT_BUFFER,
                 style=None, get_style=None,
                 key_bindings_registry=None, clipboard=None,
                 on_abort=AbortAction.RETRY, on_exit=AbortAction.IGNORE,
                 use_alternate_screen=False,

                 paste_mode=Never(), ignore_case=Never(),

                 on_input_timeout=None, on_start=None, on_stop=None,
                 on_reset=None, on_initialize=None, on_buffer_changed=None):

        assert layout is None or isinstance(layout, Layout)
        assert buffer is None or isinstance(buffer, Buffer)
        assert buffers is None or isinstance(buffers, dict)
        assert key_bindings_registry is None or isinstance(key_bindings_registry, Registry)
        assert clipboard is None or isinstance(clipboard, Clipboard)
        assert on_abort in AbortAction._all
        assert on_exit in AbortAction._all
        assert isinstance(use_alternate_screen, bool)
        assert isinstance(paste_mode, CLIFilter)
        assert isinstance(ignore_case, CLIFilter)
        assert on_start is None or isinstance(on_start, Callback)
        assert on_stop is None or isinstance(on_stop, Callback)
        assert on_reset is None or isinstance(on_reset, Callback)
        assert on_buffer_changed is None or isinstance(on_buffer_changed, Callback)
        assert on_initialize is None or isinstance(on_initialize, Callback)
        assert not (style and get_style)

        self.layout = layout or Window(BufferControl())
        self.buffer = buffer or Buffer(accept_action=AcceptAction.RETURN_DOCUMENT)
        self.buffers = buffers or {}
        self.initial_focussed_buffer = initial_focussed_buffer

        if style:
            self.get_style = lambda: style
        elif get_style:
            self.get_style = get_style
        else:
            self.get_style = lambda: DefaultStyle

        if key_bindings_registry is None:
            key_bindings_registry = Registry()
            load_basic_bindings(key_bindings_registry)
            load_emacs_bindings(key_bindings_registry)

        self.key_bindings_registry = key_bindings_registry
        self.clipboard = clipboard or Clipboard()
        self.on_abort = on_abort
        self.on_exit = on_exit
        self.use_alternate_screen = use_alternate_screen

        self.paste_mode = paste_mode
        self.ignore_case = ignore_case

        self.on_input_timeout = on_input_timeout or Callback()
        self.on_start = on_start or Callback()
        self.on_stop = on_stop or Callback()
        self.on_reset = on_reset or Callback()
        self.on_initialize = on_initialize or Callback()
        self.on_buffer_changed = on_buffer_changed or Callback()
