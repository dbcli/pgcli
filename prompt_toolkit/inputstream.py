"""
Parser for VT100 input stream.
"""
from __future__ import unicode_literals
import six

from .keys import Key

__all__ = (
    'InputStream',
    'KeyPressHistory',
)


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
        '\x00': Key.ControlSpace, # Control-Space (Also for Ctrl-@)
        '\x01': Key.ControlA, # Control-A (home)
        '\x02': Key.ControlB, # Control-B (emacs cursor left)
        '\x03': Key.ControlC, # Control-C (interrupt)
        '\x04': Key.ControlD, # Control-D (exit)
        '\x05': Key.ControlE, # Contrel-E (end)
        '\x06': Key.ControlF, # Control-F (cursor forward)
        '\x07': Key.ControlG, # Control-G
        '\x08': Key.ControlH, # Control-H (8) (Identical to '\b')
        '\x09': Key.ControlI, # Control-I (9) (Identical to '\t')
        '\x0a': Key.ControlJ, # Control-J (10) (Identical to '\n')
        '\x0b': Key.ControlK, # Control-K (delete until end of line; vertical tab)
        '\x0c': Key.ControlL, # Control-L (clear; form feed)
        '\x0d': Key.ControlM, # Control-M (13) (Identical to '\r')
        '\x0e': Key.ControlN, # Control-N (14) (history forward)
        '\x0f': Key.ControlO, # Control-O (15)
        '\x10': Key.ControlP, # Control-P (16) (history back)
        '\x11': Key.ControlQ, # Control-Q
        '\x12': Key.ControlR, # Control-R (18) (reverse search)
        '\x13': Key.ControlS, # Control-S (19) (forward search)
        '\x14': Key.ControlT, # Control-T
        '\x15': Key.ControlU, # Control-U
        '\x16': Key.ControlV, # Control-V
        '\x17': Key.ControlW, # Control-W
        '\x18': Key.ControlX, # Control-X
        '\x19': Key.ControlY, # Control-Y (25)
        '\x1a': Key.ControlZ, # Control-Z
        '\x1c': Key.ControlBackslash, # Both Control-\ and Ctrl-|
        '\x1d': Key.ControlSquareClose, # Control-]
        '\x1e': Key.ControlCircumflex, # Control-^
        '\x1f': Key.ControlUnderscore, # Control-underscore (Also for Ctrl-hypen.)
        '\x7f': Key.Backspace, # (127) Backspace
           ### '\x1b': 'escape',
        '\x1b[A': Key.Up,
        '\x1b[B': Key.Down,
        '\x1b[C': Key.Right,
        '\x1b[D': Key.Left,
        '\x1b[H': Key.Home,
        '\x1bOH': Key.Home,
        '\x1b[F': Key.End,
        '\x1bOF': Key.End,
        '\x1b[3~': Key.Delete,
        '\x1b[3;2~': Key.ShiftDelete, # xterm, gnome-terminal.
        '\x1b[1~': Key.Home, # tmux
        '\x1b[4~': Key.End, # tmux
        '\x1b[5~': Key.PageUp,
        '\x1b[6~': Key.PageDown,
        '\x1b[7~': Key.Home, # xrvt
        '\x1b[8~': Key.End, # xrvt
        '\x1b[Z': Key.BackTab, # shift + tab

        '\x1bOP': Key.F1,
        '\x1bOQ': Key.F2,
        '\x1bOR': Key.F3,
        '\x1bOS': Key.F4,
        '\x1b[15~': Key.F5,
        '\x1b[17~': Key.F6,
        '\x1b[18~': Key.F7,
        '\x1b[19~': Key.F8,
        '\x1b[20~': Key.F9,
        '\x1b[21~': Key.F10,
        '\x1b[23~': Key.F11,
        '\x1b[24~': Key.F12,
        '\x1b[25~': Key.F13,
        '\x1b[26~': Key.F14,
        '\x1b[28~': Key.F15,
        '\x1b[29~': Key.F16,
        '\x1b[31~': Key.F17,
        '\x1b[32~': Key.F18,
        '\x1b[33~': Key.F19,
        '\x1b[34~': Key.F20,

        # Meta + arrow keys. Several terminals handle this differently.
        # The following sequences are for xterm and gnome-terminal.
        #     (Iterm sends ESC followed by the normal arrow_up/down/left/right
        #     sequences, and the OSX Terminal sends ESCb and ESCf for "alt
        #     arrow_left" and "alt arrow_right." We don't handle these
        #     explicitely, in here, because would could not distinguesh between
        #     pressing ESC (to go to Vi navigation mode), followed by just the
        #     'b' or 'f' key. These combinations are handled in
        #     the input processor.)
        '\x1b[1;3D': (Key.Escape, Key.Left),
        '\x1b[1;3C': (Key.Escape, Key.Right),
        '\x1b[1;3A': (Key.Escape, Key.Up),
        '\x1b[1;3B': (Key.Escape, Key.Down),
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
                    self._call_handler(options[c])
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
                        self._call_handler(Key.Escape)
                    else:
                        self._call_handler(prefix[0])

                    buffer = prefix[1:] + c
                    break # Reset. Go back to outer loop

                # Handle letter (no match was found.)
                else:
                    self._call_handler(c)
                    break # Reset. Go back to outer loop

    def _call_handler(self, key):
        """
        Callback to handler.
        """
        if isinstance(key, tuple):
            for k in key:
                self._call_handler(k)
        else:
            self._input_processor.feed_key(key)

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
