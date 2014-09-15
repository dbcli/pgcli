"""
Parser for VT100 input stream.
"""
from __future__ import unicode_literals
import six

from .keys import Keys

__all__ = (
    'InputStream',
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
        return 'KeyPress(key=%r, data=%r)' % (self.key, self.data)


class InputStream(object):
    """
    Parser for VT100 input stream.

    Feed the data through the `feed` method and the correct callbacks of the
    `input_processor` will be called.

    ::

        h = InputStreamHandler()
        i = InputStream(h)
        i.feed('data\x01...')

    :attr input_processor: :class:`~prompt_toolkit.key_binding.InputProcessor` instance.
    """
    # Lookup table of ANSI escape sequences for a VT100 terminal
    mappings = {
        '\x00': Keys.ControlSpace, # Control-Space (Also for Ctrl-@)
        '\x01': Keys.ControlA, # Control-A (home)
        '\x02': Keys.ControlB, # Control-B (emacs cursor left)
        '\x03': Keys.ControlC, # Control-C (interrupt)
        '\x04': Keys.ControlD, # Control-D (exit)
        '\x05': Keys.ControlE, # Contrel-E (end)
        '\x06': Keys.ControlF, # Control-F (cursor forward)
        '\x07': Keys.ControlG, # Control-G
        '\x08': Keys.ControlH, # Control-H (8) (Identical to '\b')
        '\x09': Keys.ControlI, # Control-I (9) (Identical to '\t')
        '\x0a': Keys.ControlJ, # Control-J (10) (Identical to '\n')
        '\x0b': Keys.ControlK, # Control-K (delete until end of line; vertical tab)
        '\x0c': Keys.ControlL, # Control-L (clear; form feed)
        '\x0d': Keys.ControlM, # Control-M (13) (Identical to '\r')
        '\x0e': Keys.ControlN, # Control-N (14) (history forward)
        '\x0f': Keys.ControlO, # Control-O (15)
        '\x10': Keys.ControlP, # Control-P (16) (history back)
        '\x11': Keys.ControlQ, # Control-Q
        '\x12': Keys.ControlR, # Control-R (18) (reverse search)
        '\x13': Keys.ControlS, # Control-S (19) (forward search)
        '\x14': Keys.ControlT, # Control-T
        '\x15': Keys.ControlU, # Control-U
        '\x16': Keys.ControlV, # Control-V
        '\x17': Keys.ControlW, # Control-W
        '\x18': Keys.ControlX, # Control-X
        '\x19': Keys.ControlY, # Control-Y (25)
        '\x1a': Keys.ControlZ, # Control-Z

        '\x1c': Keys.ControlBackslash, # Both Control-\ and Ctrl-|
        '\x1d': Keys.ControlSquareClose, # Control-]
        '\x1e': Keys.ControlCircumflex, # Control-^
        '\x1f': Keys.ControlUnderscore, # Control-underscore (Also for Ctrl-hypen.)
        '\x7f': Keys.Backspace, # (127) Backspace
           ### '\x1b': 'escape',
        '\x1b[A': Keys.Up,
        '\x1b[B': Keys.Down,
        '\x1b[C': Keys.Right,
        '\x1b[D': Keys.Left,
        '\x1b[H': Keys.Home,
        '\x1bOH': Keys.Home,
        '\x1b[F': Keys.End,
        '\x1bOF': Keys.End,
        '\x1b[3~': Keys.Delete,
        '\x1b[3;2~': Keys.ShiftDelete, # xterm, gnome-terminal.
        '\x1b[1~': Keys.Home, # tmux
        '\x1b[4~': Keys.End, # tmux
        '\x1b[5~': Keys.PageUp,
        '\x1b[6~': Keys.PageDown,
        '\x1b[7~': Keys.Home, # xrvt
        '\x1b[8~': Keys.End, # xrvt
        '\x1b[Z': Keys.BackTab, # shift + tab

        '\x1bOP': Keys.F1,
        '\x1bOQ': Keys.F2,
        '\x1bOR': Keys.F3,
        '\x1bOS': Keys.F4,
        '\x1b[15~': Keys.F5,
        '\x1b[17~': Keys.F6,
        '\x1b[18~': Keys.F7,
        '\x1b[19~': Keys.F8,
        '\x1b[20~': Keys.F9,
        '\x1b[21~': Keys.F10,
        '\x1b[23~': Keys.F11,
        '\x1b[24~': Keys.F12,
        '\x1b[25~': Keys.F13,
        '\x1b[26~': Keys.F14,
        '\x1b[28~': Keys.F15,
        '\x1b[29~': Keys.F16,
        '\x1b[31~': Keys.F17,
        '\x1b[32~': Keys.F18,
        '\x1b[33~': Keys.F19,
        '\x1b[34~': Keys.F20,

        # Meta + arrow keys. Several terminals handle this differently.
        # The following sequences are for xterm and gnome-terminal.
        #     (Iterm sends ESC followed by the normal arrow_up/down/left/right
        #     sequences, and the OSX Terminal sends ESCb and ESCf for "alt
        #     arrow_left" and "alt arrow_right." We don't handle these
        #     explicitely, in here, because would could not distinguesh between
        #     pressing ESC (to go to Vi navigation mode), followed by just the
        #     'b' or 'f' key. These combinations are handled in
        #     the input processor.)
        '\x1b[1;3D': (Keys.Escape, Keys.Left),
        '\x1b[1;3C': (Keys.Escape, Keys.Right),
        '\x1b[1;3A': (Keys.Escape, Keys.Up),
        '\x1b[1;3B': (Keys.Escape, Keys.Down),
    }

    def __init__(self, input_processor, stdout=None):
        self._input_processor = input_processor

        # Put the terminal in cursor mode. (Instead of application mode.)
        if stdout:
            stdout.write('\x1b[?1l')
            stdout.flush()

        self.reset()

        # Put the terminal in application mode.
        #print('\x1b[?1h')

    def reset(self):
        self._start_parser()

    def _start_parser(self):
        """
        Start the parser coroutine.
        """
        self._input_parser = self._input_parser_generator()
        self._input_parser.send(None)

    def _input_parser_generator(self):
        """
        Coroutine (state machine) for the input parser.
        """
        buffer = ''

        while True:
            options = self.mappings
            prefix = ''

            while True:
                if buffer:
                    c, buffer = buffer[0], buffer[1:]
                else:
                    c = yield

                # When we have a match -> call handler
                if c in options:
                    self._call_handler(options[c], prefix + c)
                    break # Reset. Go back to outer loop

                # When the first character matches -> pop first letters in options dict
                elif any(k[0] == c for k in options.keys()):
                    options = { k[1:]: v for k, v in options.items() if k[0] == c }
                    prefix += c

                # An 'invalid' sequence, take the first char as literal, and
                # start processing the rest again by shifting it in a temp
                # variable.
                elif prefix:
                    if prefix[0] == '\x1b':
                        self._call_handler(Keys.Escape, prefix[0])
                    else:
                        self._call_handler(prefix[0], prefix[0])

                    buffer = prefix[1:] + c
                    break # Reset. Go back to outer loop

                # Handle letter (no match was found.)
                else:
                    self._call_handler(c, c)
                    break # Reset. Go back to outer loop

    def _call_handler(self, key, insert_text):
        """
        Callback to handler.
        """
        if isinstance(key, tuple):
            for k in key:
                self._call_handler(k, insert_text)
        else:
            self._input_processor.feed_key(KeyPress(key, insert_text))

    def feed(self, data):
        """
        Feed the input stream.
        """
        assert isinstance(data, six.text_type)

        #print(repr(data))

        try:
            for c in data:
                self._input_parser.send(c)
        except Exception as e:
            # Restart the parser in case of an exception.
            # (The parse coroutine will go into `StopIteration` otherwise.)
            self._start_parser()
            raise
