# *** encoding: utf-8 ***
"""
An :class:`~.InputProcessor` receives callbacks for the keystrokes parsed from
the input in the :class:`~prompt_toolkit.inputstream.InputStream` instance.

The `InputProcessor` will according to the implemented keybindings call the
correct callbacks when new key presses are feed through `feed_key`.
"""
from __future__ import unicode_literals
from .keys import Key
from .enums import InputMode

__all__ = (
    'Registry',
    'InputProcessor',
)


class InputProcessor(object):
    def __init__(self, registry, default_input_mode=InputMode.INPUT):
        self._registry = registry
        self.default_input_mode = default_input_mode

    def reset(self):
        self._previous_key_sequence = None
        self.input_mode = self.default_input_mode

        self._process_coroutine = self._process()
        self._process_coroutine.send(None)

        #: Readline argument (for repetition of commands.)
        #: https://www.gnu.org/software/bash/manual/html_node/Readline-Arguments.html
        self.arg = None

    def _process(self):
        """
        Coroutine for the processing of key presses.
        """
        def is_active(binding):
            return binding.input_mode in (None, self.input_mode)

        buffer = []

        while True:
            # Start with all the active bindings.
            # (In reverse order, because we want to give priority to bindings
            # that are defined later.)
            options = [ (b.keys, b) for b in self._registry.key_bindings[::-1] if is_active(b) ]

            processing = []

            while True:
                # Receive next key press.
                if buffer:
                    key_press, buffer = buffer[0], buffer[1:]
                else:
                    key_press = yield

                key_sequence = processing + [key_press]

                # Matches
                exact_matches_with_mode = [(k, b) for k, b in options if k == (key_press,) and b.input_mode ]
                exact_matches = [(k, b) for k, b in options if k == (key_press,)]
                prefix_matches = [(k, b) for k, b in options if k[0] == key_press and len(k) > 1]
                any_matches_with_mode = [(k, b) for k, b in options if k == (Key.Any,) and b.input_mode ]
                any_matches = [(k, b) for k, b in options if k == (Key.Any,)]

                # If we have an exact match, call handler.
                # (An exact match that specifies the input mode will always get higher priority.)
                if exact_matches_with_mode or exact_matches:
                    self._call_handler((exact_matches_with_mode or exact_matches)[0][1], key_sequence=key_sequence)
                    break # Reset. Go back to outer loop.

                # When the prefix matches -> pop first keys from options dict.
                elif prefix_matches:
                    options = [(k[1:], b) for k, b in prefix_matches]
                    processing.append(key_press)

                # If we have `Key.Any`, that should catch all keys (If there is
                # no other match) and pass the pressed key to the handler.
                elif any_matches_with_mode or any_matches:
                    self._call_handler((any_matches_with_mode or any_matches)[0][1],
                                    key_sequence=key_sequence, data=key_press)
                    break

                # An 'invalid' sequence, ignore the first key_press and start
                # processing the rest again by shifting in a temp variable.
                else:
                    buffer = (processing + buffer)[1:]
                    break

    def _call_handler(self, handler, data=None, key_sequence=None):
        arg = self.arg
        self.arg = None

        event = Event(self, arg=arg, data=data, previous_key_sequence=self._previous_key_sequence)
        handler.call(event)

        for h in self._registry.after_handler_callbacks:
            h(event)

        self._previous_key_sequence = key_sequence

    def feed_key(self, key_press):
        self._process_coroutine.send(key_press)


class Event(object):
    def __init__(self, input_processor, arg=None, data=None, key_sequence=None, previous_key_sequence=None):
        self.input_processor = input_processor
        self.data = data
        self.key_sequence = key_sequence
        self.previous_key_sequence = previous_key_sequence
        self._arg = arg

    @property
    def arg(self):
        return self._arg or 1

    @property
    def second_press(self):
        return self.key_sequence == self.previous_key_sequence

    def append_to_arg_count(self, data):
        """
        Add digit to the input argument.

        :param data: the typed digit as string
        """
        assert data in '-0123456789'
        current = self._arg

        if current is None:
            if data == '-':
                data = '-1'
            result = int(data)
        else:
            result = int("%s%s" % (current, data))

        # Don't exceed a million.
        if int(result) >= 1000000:
            result = None

        self.input_processor.arg = result


class _Binding(object):
    def __init__(self, keys, callable, input_mode=None):
        self.keys = keys
        self._callable = callable
        self.input_mode = input_mode

    def call(self, event):
        return self._callable(event)


class Registry(object):
    """
    Key binding registry.
    """
    def __init__(self):
        self.key_bindings = []
        self.after_handler_callbacks = []

    def add_binding(self, *keys, **kwargs):
        """
        Decorator for annotating key bindings.
        """
        input_mode = kwargs.pop('in_mode', None)
        assert not kwargs
        assert keys

        def decorator(func):
            self.key_bindings.append(_Binding(keys, func, input_mode=input_mode))
            return func
        return decorator

    def add_after_handler_callback(self, callback):
        self.after_handler_callbacks.append(callback)
