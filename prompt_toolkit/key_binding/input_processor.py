# *** encoding: utf-8 ***
"""
An :class:`~.InputProcessor` receives callbacks for the keystrokes parsed from
the input in the :class:`~prompt_toolkit.inputstream.InputStream` instance.

The `InputProcessor` will according to the implemented keybindings call the
correct callbacks when new key presses are feed through `feed_key`.
"""
from __future__ import unicode_literals
from ..keys import Keys
from ..utils import Callback
from prompt_toolkit.buffer import EditReadOnlyBuffer

import weakref

__all__ = (
    'InputProcessor',
    'KeyPress',
)


class KeyPress(object):
    """
    :param key: a `Keys` instance.
    :param data: The received string on stdin. (Often vt100 escape codes.)
    """
    def __init__(self, key, data):
        self.key = key
        self.data = data

    def __repr__(self):
        return '%s(key=%r, data=%r)' % (
            self.__class__.__name__, self.key, self.data)

    def __eq__(self, other):
        return self.key == other.key and self.data == other.data


class InputProcessor(object):
    """
    Statemachine that receives :class:`KeyPress` instances and according to the
    key bindings in the given :class:`Registry`, calls the matching handlers.

    ::

        p = InputProcessor(registry)

        # Send keys into the processor.
        p.feed_key(KeyPress(Keys.ControlX, '\x18'))
        p.feed_key(KeyPress(Keys.ControlC, '\x03')

        # Now the ControlX-ControlC callback will be called if this sequence is
        # registered in the registry.

    :param registry: `Registry` instance.
    :param cli_ref: weakref to `CommandLineInterface`.
    """
    def __init__(self, registry, cli_ref):
        self._registry = registry
        self._cli_ref = cli_ref
        self.reset()

        self.beforeKeyPress = Callback()
        self.afterKeyPress = Callback()

#        print(' '.join(set(''.join(map(str, kb.keys)) for kb in registry.key_bindings if all(isinstance(X, unicode) for X in kb.keys))))

    def reset(self):
        self._previous_key_sequence = None
        self._previous_handler = None

        self._process_coroutine = self._process()
        self._process_coroutine.send(None)

        #: Readline argument (for repetition of commands.)
        #: https://www.gnu.org/software/bash/manual/html_node/Readline-Arguments.html
        self.arg = None

    def _get_matches(self, key_presses):
        """
        For a list of :class:`KeyPress` instances. Give the matching handlers
        that would handle this.
        """
        keys = tuple(k.key for k in key_presses)
        cli = self._cli_ref()

        # Try match, with mode flag
        with_mode = [b for b in self._registry.get_bindings_for_keys(keys) if b.filter(cli)]
        if with_mode:
            return with_mode

        # Try match, where the last key is replaced with 'Any', with mode.
        keys_any = tuple(keys[:-1] + (Keys.Any,))

        with_mode_any = [b for b in self._registry.get_bindings_for_keys(keys_any) if b.filter(cli)]
        if with_mode_any:
            return with_mode_any

        return []

    def _is_prefix_of_longer_match(self, key_presses):
        """
        For a list of :class:`KeyPress` instances. Return True if there is any
        handler that is bound to a suffix of this keys.
        """
        keys = tuple(k.key for k in key_presses)
        cli = self._cli_ref()

        # Get the filters for all the key bindings that have a longer match.
        # Note that we transform it into a `set`, because we don't care about
        # the actual bindings and executing it more than once doesn't make
        # sense. (Many key bindings share the same filter.)
        filters = set(b.filter for b in self._registry.get_bindings_starting_with_keys(keys))

        # When any key binding is active, return True.
        return any(f(cli) for f in filters)

    def _process(self):
        """
        Coroutine implementing the key match algorithm. Key strokes are sent
        into this generator, and it calls the appropriate handlers.
        """
        buffer = []
        retry = False

        while True:
            if retry:
                retry = False
            else:
                buffer.append((yield))

            # If we have some key presses, check for matches.
            if buffer:
                is_prefix_of_longer_match = self._is_prefix_of_longer_match(buffer)
                matches = self._get_matches(buffer)

                # When longer matches were found, but the current match is
                # 'eager', ignore all the longer matches.
                if matches and matches[-1].eager(self._cli_ref()):
                    is_prefix_of_longer_match = False

                # Exact matches found, call handler.
                if not is_prefix_of_longer_match and matches:
                    self._call_handler(matches[-1], key_sequence=buffer)
                    buffer = []

                # No match found.
                elif not is_prefix_of_longer_match and not matches:
                    retry = True
                    found = False

                    # Loop over the input, try longest match first and shift.
                    for i in range(len(buffer), 0, -1):
                        matches = self._get_matches(buffer[:i])
                        if matches:
                            self._call_handler(matches[-1], key_sequence=buffer[:i])
                            buffer = buffer[i:]
                            found = True

                    if not found:
                        buffer = buffer[1:]

    def feed_key(self, key_press):
        """
        Send a new :class:`KeyPress` into this processor.
        """
        assert isinstance(key_press, KeyPress)

        if key_press.key != Keys.CPRResponse:
            self.beforeKeyPress.fire()

        self._process_coroutine.send(key_press)

        if key_press.key != Keys.CPRResponse:
            self.afterKeyPress.fire()

    def _call_handler(self, handler, key_sequence=None):
        arg = self.arg
        self.arg = None

        is_repeat = handler == self._previous_handler

        try:
            event = Event(weakref.ref(self), arg=arg, key_sequence=key_sequence,
                          previous_key_sequence=self._previous_key_sequence,
                          is_repeat=is_repeat)
            handler.call(event)
            self._registry.on_handler_called.fire(event)

        except EditReadOnlyBuffer:
            # When a key binding does an attempt to change a buffer which is read-only,
            # we can just silently ignore that.
            pass

        self._previous_key_sequence = key_sequence
        self._previous_handler = handler


class Event(object):
    """
    Key press event, delivered to key bindings.

    :param input_processor_ref: Weak reference to the `InputProcessor`.
    :param arg: Repetition argument.
    :param key_sequence: List of `KeyPress` instances.
    :param previouskey_sequence: Previous list of `KeyPress` instances.
    :param is_repeat: True when the previous event was delivered to the same handler.
    """
    def __init__(self, input_processor_ref, arg=None, key_sequence=None,
            previous_key_sequence=None, is_repeat=False):
        self._input_processor_ref = input_processor_ref
        self.key_sequence = key_sequence
        self.previous_key_sequence = previous_key_sequence

        #: True when the previous key sequence was handled by the same handler.
        self.is_repeat = is_repeat

        self._arg = arg

    def __repr__(self):
        return 'Event(arg=%r, key_sequence=%r, is_repeat=%r)' % (
                self.arg, self.key_sequence, self.is_repeat)

    @property
    def data(self):
        return self.key_sequence[-1].data

    @property
    def input_processor(self):
        return self._input_processor_ref()

    @property
    def cli(self):
        """
        Command line interface.
        """
        return self.input_processor._cli_ref()

    @property
    def current_buffer(self):
        """
        The current buffer.
        """
        return self.cli.current_buffer

    @property
    def arg(self):
        """
        Repetition argument.
        """
        return self._arg or 1

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
