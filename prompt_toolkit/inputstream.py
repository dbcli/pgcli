"""
Parser for VT100 input stream.
"""
from __future__ import unicode_literals
import six

__all__ = ('InputStream', )


class InputStream(object):
    """
    Parser for VT100 input stream.

    Feed the data through the `feed` method and the correct callbacks of the
    `inputstream_handler` will be called.

    ::

        h = InputStreamHandler()
        i = InputStream(h)
        i.feed('data\x01...')

    :attr handler: :class:`~prompt_toolkit.inputstream_handler.InputStreamHandler` instance.
    """
    # Lookup table of ANSI escape sequences for a VT100 terminal
    CALLBACKS = {
        '\x00': 'ctrl_space', # Control-Space (Also for Ctrl-@)
        '\x01': 'ctrl_a', # Control-A (home)
        '\x02': 'ctrl_b', # Control-B (emacs cursor left)
        '\x03': 'ctrl_c', # Control-C (interrupt)
        '\x04': 'ctrl_d', # Control-D (exit)
        '\x05': 'ctrl_e', # Contrel-E (end)
        '\x06': 'ctrl_f', # Control-F (cursor forward)
        '\x07': 'ctrl_g', # Control-G
        '\x08': 'ctrl_h', # Control-H (8) (Identical to '\b')
        '\x09': 'ctrl_i', # Control-I (9) (Identical to '\t')
        '\x0a': 'ctrl_j', # Control-J (10) (Identical to '\n')
        '\x0b': 'ctrl_k', # Control-K (delete until end of line; vertical tab)
        '\x0c': 'ctrl_l', # Control-L (clear; form feed)
        '\x0d': 'ctrl_m', # Control-M (13) (Identical to '\r')
        '\x0e': 'ctrl_n', # Control-N (14) (history forward)
        '\x0f': 'ctrl_o', # Control-O (15)
        '\x10': 'ctrl_p', # Control-P (16) (history back)
        '\x11': 'ctrl_q', # Control-Q
        '\x12': 'ctrl_r', # Control-R (18) (reverse search)
        '\x13': 'ctrl_s', # Control-S (19) (forward search)
        '\x14': 'ctrl_t', # Control-T
        '\x15': 'ctrl_u', # Control-U
        '\x16': 'ctrl_v', # Control-V
        '\x17': 'ctrl_w', # Control-W
        '\x18': 'ctrl_x', # Control-X
        '\x19': 'ctrl_y', # Control-Y (25)
        '\x1a': 'ctrl_z', # Control-Z
        '\x1c': 'ctrl_backslash', # Both Control-\ and Ctrl-|
        '\x1d': 'ctrl_square_close', # Control-]
        '\x1e': 'ctrl_circumflex', # Control-^
        '\x1f': 'ctrl_underscore', # Control-underscore (Also for Ctrl-hypen.)
        '\x7f': 'backspace', # (127) Backspace
           ### '\x1b': 'escape',
        '\x1b[A': 'arrow_up',
        '\x1b[B': 'arrow_down',
        '\x1b[C': 'arrow_right',
        '\x1b[D': 'arrow_left',
        '\x1b[H': 'home',
        '\x1bOH': 'home',
        '\x1b[F': 'end',
        '\x1bOF': 'end',
        '\x1b[3~': 'delete',
        '\x1b[3;2~': 'shift_delete', # xterm, gnome-terminal.
        '\x1b[1~': 'home', # tmux
        '\x1b[4~': 'end', # tmux
        '\x1b[5~': 'page_up',
        '\x1b[6~': 'page_down',
        '\x1b[7~': 'home', # xrvt
        '\x1b[8~': 'end', # xrvt
        '\x1b[Z': 'backtab', # shift + tab

        '\x1bOP': 'F1',
        '\x1bOQ': 'F2',
        '\x1bOR': 'F3',
        '\x1bOS': 'F4',
        '\x1b[15~': 'F5',
        '\x1b[17~': 'F6',
        '\x1b[18~': 'F7',
        '\x1b[19~': 'F8',
        '\x1b[20~': 'F9',
        '\x1b[21~': 'F10',
        '\x1b[23~': 'F11',
        '\x1b[24~': 'F12',
        '\x1b[25~': 'F13',
        '\x1b[26~': 'F14',
        '\x1b[28~': 'F15',
        '\x1b[29~': 'F16',
        '\x1b[31~': 'F17',
        '\x1b[32~': 'F18',
        '\x1b[33~': 'F19',
        '\x1b[34~': 'F20',

        # Meta + arrow keys. Several terminals handle this differently.
        # The following sequences are for xterm and gnome-terminal.
        #     (Iterm sends ESC followed by the normal arrow_up/down/left/right
        #     sequences, and the OSX Terminal sends ESCb and ESCf for "alt
        #     arrow_left" and "alt arrow_right." We don't handle these
        #     explicitely, in here, because would could not distinguesh between
        #     pressing ESC (to go to Vi navigation mode), followed by just the
        #     'b' or 'f' key. These combinations are handled in
        #     inputstream_handler.)
        '\x1b[1;3D': 'meta_arrow_left',
        '\x1b[1;3C': 'meta_arrow_right',
        '\x1b[1;3A': 'meta_arrow_up',
        '\x1b[1;3B': 'meta_arrow_down',
    }

    def __init__(self, handler, stdout=None):
        self._start_parser()
        self._handler = handler

        # Put the terminal in cursor mode. (Instead of application mode.)
        if stdout:
            stdout.write('\x1b[?1l')
            stdout.flush()

        # Put the terminal in application mode.
        #print('\x1b[?1h')

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
            options = self.CALLBACKS
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
                elif c in [ k[0] for k in options.keys() ]:
                    options = { k[1:]: v for k, v in options.items() if k[0] == c }
                    prefix += c

                # An 'invalid' sequence, take the first char as literal, and
                # start processing the rest again by shifting it in a temp
                # variable.
                elif prefix:
                    if prefix[0] == '\x1b':
                        self._call_handler('escape')
                    else:
                        self._call_handler('insert_char', prefix[0])

                    buffer = prefix[1:] + c
                    break # Reset. Go back to outer loop

                # Handle letter (no match was found.)
                else:
                    self._call_handler('insert_char', c)
                    break # Reset. Go back to outer loop

    def _call_handler(self, name, *a):
        """
        Callback to handler.
        """
        self._handler(name, *a)

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
