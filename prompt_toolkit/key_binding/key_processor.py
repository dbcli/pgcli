# *** encoding: utf-8 ***
"""
An :class:`~.KeyProcessor` receives callbacks for the keystrokes parsed from
the input in the :class:`~prompt_toolkit.inputstream.InputStream` instance.

The `KeyProcessor` will according to the implemented keybindings call the
correct callbacks when new key presses are feed through `feed`.
"""
from __future__ import unicode_literals
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import EditReadOnlyBuffer
from prompt_toolkit.filters.app import vi_navigation_mode
from prompt_toolkit.keys import Keys, ALL_KEYS
from prompt_toolkit.utils import Event
from prompt_toolkit.eventloop import run_in_executor, call_from_executor

from .key_bindings import KeyBindingsBase

from collections import deque
from six.moves import range
import six
import time
import weakref

__all__ = [
    'KeyProcessor',
    'KeyPress',
    'KeyPressEvent',
]


class KeyPress(object):
    """
    :param key: A `Keys` instance or text (one character).
    :param data: The received string on stdin. (Often vt100 escape codes.)
    """
    def __init__(self, key, data=None):
        assert key in ALL_KEYS or len(key) == 1
        assert data is None or isinstance(data, six.text_type)

        if data is None:
            data = key

        self.key = key
        self.data = data

    def __repr__(self):
        return '%s(key=%r, data=%r)' % (
            self.__class__.__name__, self.key, self.data)

    def __eq__(self, other):
        return self.key == other.key and self.data == other.data


"""
Helper object to indicate flush operation in the KeyProcessor.
NOTE: the implementation is very similar to the VT100 parser.
"""
_Flush = KeyPress('?', data='_Flush')


class KeyProcessor(object):
    """
    Statemachine that receives :class:`KeyPress` instances and according to the
    key bindings in the given :class:`KeyBindings`, calls the matching handlers.

    ::

        p = KeyProcessor(key_bindings)

        # Send keys into the processor.
        p.feed(KeyPress(Keys.ControlX, '\x18'))
        p.feed(KeyPress(Keys.ControlC, '\x03')

        # Process all the keys in the queue.
        p.process_keys()

        # Now the ControlX-ControlC callback will be called if this sequence is
        # registered in the key bindings.

    :param key_bindings: `KeyBindingsBase` instance.
    """
    def __init__(self, key_bindings):
        assert isinstance(key_bindings, KeyBindingsBase)

        self._bindings = key_bindings

        self.before_key_press = Event(self)
        self.after_key_press = Event(self)

        self._keys_pressed = 0  # Monotonically increasing counter.

        self.reset()

    def reset(self):
        self._previous_key_sequence = []
        self._previous_handler = None

        # The queue of keys not yet send to our _process generator/state machine.
        self.input_queue = deque()

        # The key buffer that is matched in the generator state machine.
        # (This is at at most the amount of keys that make up for one key binding.)
        self.key_buffer = []

        #: Readline argument (for repetition of commands.)
        #: https://www.gnu.org/software/bash/manual/html_node/Readline-Arguments.html
        self.arg = None

        # Start the processor coroutine.
        self._process_coroutine = self._process()
        self._process_coroutine.send(None)

    def _get_matches(self, key_presses):
        """
        For a list of :class:`KeyPress` instances. Give the matching handlers
        that would handle this.
        """
        keys = tuple(k.key for k in key_presses)

        # Try match, with mode flag
        return [b for b in self._bindings.get_bindings_for_keys(keys) if b.filter()]

    def _is_prefix_of_longer_match(self, key_presses):
        """
        For a list of :class:`KeyPress` instances. Return True if there is any
        handler that is bound to a suffix of this keys.
        """
        keys = tuple(k.key for k in key_presses)

        # Get the filters for all the key bindings that have a longer match.
        # Note that we transform it into a `set`, because we don't care about
        # the actual bindings and executing it more than once doesn't make
        # sense. (Many key bindings share the same filter.)
        filters = set(b.filter for b in self._bindings.get_bindings_starting_with_keys(keys))

        # When any key binding is active, return True.
        return any(f() for f in filters)

    def _process(self):
        """
        Coroutine implementing the key match algorithm. Key strokes are sent
        into this generator, and it calls the appropriate handlers.
        """
        buffer = self.key_buffer
        retry = False

        while True:
            flush = False

            if retry:
                retry = False
            else:
                key = yield
                if key is _Flush:
                    flush = True
                else:
                    buffer.append(key)

            # If we have some key presses, check for matches.
            if buffer:
                matches = self._get_matches(buffer)

                if flush:
                    is_prefix_of_longer_match = False
                else:
                    is_prefix_of_longer_match = self._is_prefix_of_longer_match(buffer)

                # When eager matches were found, give priority to them and also
                # ignore all the longer matches.
                eager_matches = [m for m in matches if m.eager()]

                if eager_matches:
                    matches = eager_matches
                    is_prefix_of_longer_match = False

                # Exact matches found, call handler.
                if not is_prefix_of_longer_match and matches:
                    self._call_handler(matches[-1], key_sequence=buffer[:])
                    del buffer[:]  # Keep reference.

                # No match found.
                elif not is_prefix_of_longer_match and not matches:
                    retry = True
                    found = False

                    # Loop over the input, try longest match first and shift.
                    for i in range(len(buffer), 0, -1):
                        matches = self._get_matches(buffer[:i])
                        if matches:
                            self._call_handler(matches[-1], key_sequence=buffer[:i])
                            del buffer[:i]
                            found = True
                            break

                    if not found:
                        del buffer[:1]

    def feed(self, key_press, first=False):
        """
        Add a new :class:`KeyPress` to the input queue.
        (Don't forget to call `process_keys` in order to process the queue.)

        :param first: If true, insert before everything else.
        """
        assert isinstance(key_press, KeyPress)
        self._keys_pressed += 1

        if first:
            self.input_queue.appendleft(key_press)
        else:
            self.input_queue.append(key_press)

    def feed_multiple(self, key_presses, first=False):
        """
        :param first: If true, insert before everything else.
        """
        self._keys_pressed += len(key_presses)

        if first:
            self.input_queue.extendleft(reversed(key_presses))
        else:
            self.input_queue.extend(key_presses)

    def process_keys(self):
        """
        Process all the keys in the `input_queue`.
        (To be called after `feed`.)

        Note: because of the `feed`/`process_keys` separation, it is
              possible to call `feed` from inside a key binding.
              This function keeps looping until the queue is empty.
        """
        app = get_app()

        def not_empty():
            # When the application result is set, stop processing keys.  (E.g.
            # if ENTER was received, followed by a few additional key strokes,
            # leave the other keys in the queue.)
            if app.is_done:
                # But if there are still CPRResponse keys in the queue, these
                # need to be processed.
                return any(k for k in self.input_queue if k.key == Keys.CPRResponse)
            else:
                return bool(self.input_queue)

        def get_next():
            if app.is_done:
                # Only process CPR responses. Everything else is typeahead.
                cpr = [k for k in self.input_queue if k.key == Keys.CPRResponse][0]
                self.input_queue.remove(cpr)
                return cpr
            else:
                return self.input_queue.popleft()

        keys_processed = False
        is_flush = False

        while not_empty():
            keys_processed = True

            # Process next key.
            key_press = get_next()

            is_flush = key_press is _Flush
            is_cpr = key_press.key == Keys.CPRResponse

            if not is_flush and not is_cpr:
                self.before_key_press.fire()

            try:
                self._process_coroutine.send(key_press)
            except Exception:
                # If for some reason something goes wrong in the parser, (maybe
                # an exception was raised) restart the processor for next time.
                self.reset()
                self.empty_queue()
                app.invalidate()
                raise

            if not is_flush and not is_cpr:
                self.after_key_press.fire()

        if keys_processed:
            # Invalidate user interface.
            app.invalidate()

        # Skip timeout if the last key was flush.
        if not is_flush:
            self._start_timeout()

    def empty_queue(self):
        """
        Empty the input queue. Return the unprocessed input.
        """
        key_presses = list(self.input_queue)
        self.input_queue.clear()

        # Filter out CPRs. We don't want to return these.
        key_presses = [k for k in key_presses if k.key != Keys.CPRResponse]
        return key_presses

    def _call_handler(self, handler, key_sequence=None):
        app = get_app()
        was_recording_emacs = app.emacs_state.is_recording
        was_recording_vi = bool(app.vi_state.recording_register)
        arg = self.arg
        self.arg = None

        event = KeyPressEvent(
            weakref.ref(self), arg=arg, key_sequence=key_sequence,
            previous_key_sequence=self._previous_key_sequence,
            is_repeat=(handler == self._previous_handler))

        # Save the state of the current buffer.
        if handler.save_before(event):
            event.app.current_buffer.save_to_undo_stack()

        # Call handler.
        try:
            handler.call(event)
            self._fix_vi_cursor_position(event)

        except EditReadOnlyBuffer:
            # When a key binding does an attempt to change a buffer which is
            # read-only, we can just silently ignore that.
            pass

        self._previous_key_sequence = key_sequence
        self._previous_handler = handler

        # Record the key sequence in our macro. (Only if we're in macro mode
        # before and after executing the key.)
        if handler.record_in_macro():
            if app.emacs_state.is_recording and was_recording_emacs:
                app.emacs_state.current_recording.extend(key_sequence)

            if app.vi_state.recording_register and was_recording_vi:
                for k in key_sequence:
                    app.vi_state.current_recording += k.data

    def _fix_vi_cursor_position(self, event):
        """
        After every command, make sure that if we are in Vi navigation mode, we
        never put the cursor after the last character of a line. (Unless it's
        an empty line.)
        """
        app = get_app()
        buff = app.current_buffer
        preferred_column = buff.preferred_column

        if (vi_navigation_mode() and
                buff.document.is_cursor_at_the_end_of_line and
                len(buff.document.current_line) > 0):
            buff.cursor_position -= 1

            # Set the preferred_column for arrow up/down again.
            # (This was cleared after changing the cursor position.)
            buff.preferred_column = preferred_column

    def _start_timeout(self):
        """
        Start auto flush timeout. Similar to Vim's `timeoutlen` option.

        Start a background thread with a timer. When this timeout expires and
        no key was pressed in the meantime, we flush all data in the queue and
        call the appropriate key binding handlers.
        """
        timeout = get_app().timeoutlen

        if timeout is None:
            return

        counter = self._keys_pressed

        def wait():
            " Wait for timeout. "
            time.sleep(timeout)

            if len(self.key_buffer) > 0 and counter == self._keys_pressed:
                # (No keys pressed in the meantime.)
                call_from_executor(flush_keys)

        def flush_keys():
            " Flush keys. "
            self.feed(_Flush)
            self.process_keys()

        # Automatically flush keys.
        # (_daemon needs to be set, otherwise, this will hang the
        # application for .5 seconds before exiting.)
        run_in_executor(wait, _daemon=True)


class KeyPressEvent(object):
    """
    Key press event, delivered to key bindings.

    :param key_processor_ref: Weak reference to the `KeyProcessor`.
    :param arg: Repetition argument.
    :param key_sequence: List of `KeyPress` instances.
    :param previouskey_sequence: Previous list of `KeyPress` instances.
    :param is_repeat: True when the previous event was delivered to the same handler.
    """
    def __init__(self, key_processor_ref, arg=None, key_sequence=None,
            previous_key_sequence=None, is_repeat=False):
        self._key_processor_ref = key_processor_ref
        self.key_sequence = key_sequence
        self.previous_key_sequence = previous_key_sequence

        #: True when the previous key sequence was handled by the same handler.
        self.is_repeat = is_repeat

        self._arg = arg
        self._app = get_app()

    def __repr__(self):
        return 'KeyPressEvent(arg=%r, key_sequence=%r, is_repeat=%r)' % (
                self.arg, self.key_sequence, self.is_repeat)

    @property
    def data(self):
        return self.key_sequence[-1].data

    @property
    def key_processor(self):
        return self._key_processor_ref()

    @property
    def app(self):
        """
        The current `Application` object.
        """
        return self._app

    @property
    def current_buffer(self):
        """
        The current buffer.
        """
        return self.app.current_buffer

    @property
    def arg(self):
        """
        Repetition argument.
        """
        if self._arg == '-':
            return -1

        result = int(self._arg or 1)

        # Don't exceed a million.
        if int(result) >= 1000000:
            result = 1

        return result

    @property
    def arg_present(self):
        """
        True if repetition argument was explicitly provided.
        """
        return self._arg is not None

    def append_to_arg_count(self, data):
        """
        Add digit to the input argument.

        :param data: the typed digit as string
        """
        assert data in '-0123456789'
        current = self._arg

        if data == '-':
            assert current is None or current == '-'
            result = data
        elif current is None:
            result = data
        else:
            result = "%s%s" % (current, data)

        self.key_processor.arg = result

    @property
    def cli(self):
        " For backward-compatibility. "
        return self.app
