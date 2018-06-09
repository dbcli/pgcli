"""
Mappings from VT100 (ANSI) escape sequences to the corresponding prompt_toolkit
keys.
"""
from __future__ import unicode_literals
from ..keys import Keys

__all__ = [
    'ANSI_SEQUENCES',
    'REVERSE_ANSI_SEQUENCES',
]


# Mapping of vt100 escape codes to Keys.
ANSI_SEQUENCES = {
    '\x00': Keys.ControlAt,  # Control-At (Also for Ctrl-Space)
    '\x01': Keys.ControlA,  # Control-A (home)
    '\x02': Keys.ControlB,  # Control-B (emacs cursor left)
    '\x03': Keys.ControlC,  # Control-C (interrupt)
    '\x04': Keys.ControlD,  # Control-D (exit)
    '\x05': Keys.ControlE,  # Control-E (end)
    '\x06': Keys.ControlF,  # Control-F (cursor forward)
    '\x07': Keys.ControlG,  # Control-G
    '\x08': Keys.ControlH,  # Control-H (8) (Identical to '\b')
    '\x09': Keys.ControlI,  # Control-I (9) (Identical to '\t')
    '\x0a': Keys.ControlJ,  # Control-J (10) (Identical to '\n')
    '\x0b': Keys.ControlK,  # Control-K (delete until end of line; vertical tab)
    '\x0c': Keys.ControlL,  # Control-L (clear; form feed)
    '\x0d': Keys.ControlM,  # Control-M (13) (Identical to '\r')
    '\x0e': Keys.ControlN,  # Control-N (14) (history forward)
    '\x0f': Keys.ControlO,  # Control-O (15)
    '\x10': Keys.ControlP,  # Control-P (16) (history back)
    '\x11': Keys.ControlQ,  # Control-Q
    '\x12': Keys.ControlR,  # Control-R (18) (reverse search)
    '\x13': Keys.ControlS,  # Control-S (19) (forward search)
    '\x14': Keys.ControlT,  # Control-T
    '\x15': Keys.ControlU,  # Control-U
    '\x16': Keys.ControlV,  # Control-V
    '\x17': Keys.ControlW,  # Control-W
    '\x18': Keys.ControlX,  # Control-X
    '\x19': Keys.ControlY,  # Control-Y (25)
    '\x1a': Keys.ControlZ,  # Control-Z

    '\x1b': Keys.Escape,            # Also Control-[
    '\x1c': Keys.ControlBackslash,  # Both Control-\ (also Ctrl-| )
    '\x1d': Keys.ControlSquareClose,  # Control-]
    '\x1e': Keys.ControlCircumflex,  # Control-^
    '\x1f': Keys.ControlUnderscore,  # Control-underscore (Also for Ctrl-hyphen.)

    # ASCII Delete (0x7f)
    # Vt220 (and Linux terminal) send this when pressing backspace. We map this
    # to ControlH, because that will make it easier to create key bindings that
    # work everywhere, with the trade-off that it's no longer possible to
    # handle backspace and control-h individually for the few terminals that
    # support it. (Most terminals send ControlH when backspace is pressed.)
    # See: http://www.ibb.net/~anne/keyboard.html
    '\x7f': Keys.ControlH,

    '\x1b[A': Keys.Up,
    '\x1b[B': Keys.Down,
    '\x1b[C': Keys.Right,
    '\x1b[D': Keys.Left,
    '\x1b[H': Keys.Home,
    '\x1bOH': Keys.Home,
    '\x1b[F': Keys.End,
    '\x1bOF': Keys.End,
    '\x1b[3~': Keys.Delete,
    '\x1b[3;2~': Keys.ShiftDelete,  # xterm, gnome-terminal.
    '\x1b[3;5~': Keys.ControlDelete,  # xterm, gnome-terminal.
    '\x1b[1~': Keys.Home,  # tmux
    '\x1b[4~': Keys.End,  # tmux
    '\x1b[5~': Keys.PageUp,
    '\x1b[6~': Keys.PageDown,
    '\x1b[7~': Keys.Home,  # xrvt
    '\x1b[8~': Keys.End,  # xrvt
    '\x1b[Z': Keys.BackTab,  # shift + tab
    '\x1b[2~': Keys.Insert,

    '\x1bOP': Keys.F1,
    '\x1bOQ': Keys.F2,
    '\x1bOR': Keys.F3,
    '\x1bOS': Keys.F4,
    '\x1b[[A': Keys.F1,  # Linux console.
    '\x1b[[B': Keys.F2,  # Linux console.
    '\x1b[[C': Keys.F3,  # Linux console.
    '\x1b[[D': Keys.F4,  # Linux console.
    '\x1b[[E': Keys.F5,  # Linux console.
    '\x1b[11~': Keys.F1,  # rxvt-unicode
    '\x1b[12~': Keys.F2,  # rxvt-unicode
    '\x1b[13~': Keys.F3,  # rxvt-unicode
    '\x1b[14~': Keys.F4,  # rxvt-unicode
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

    # Xterm
    '\x1b[1;2P': Keys.F13,
    '\x1b[1;2Q': Keys.F14,
    # '\x1b[1;2R': Keys.F15,  # Conflicts with CPR response.
    '\x1b[1;2S': Keys.F16,
    '\x1b[15;2~': Keys.F17,
    '\x1b[17;2~': Keys.F18,
    '\x1b[18;2~': Keys.F19,
    '\x1b[19;2~': Keys.F20,
    '\x1b[20;2~': Keys.F21,
    '\x1b[21;2~': Keys.F22,
    '\x1b[23;2~': Keys.F23,
    '\x1b[24;2~': Keys.F24,

    '\x1b[1;5A': Keys.ControlUp,     # Cursor Mode
    '\x1b[1;5B': Keys.ControlDown,   # Cursor Mode
    '\x1b[1;5C': Keys.ControlRight,  # Cursor Mode
    '\x1b[1;5D': Keys.ControlLeft,   # Cursor Mode

    '\x1b[1;2A': Keys.ShiftUp,
    '\x1b[1;2B': Keys.ShiftDown,
    '\x1b[1;2C': Keys.ShiftRight,
    '\x1b[1;2D': Keys.ShiftLeft,

    # Tmux sends following keystrokes when control+arrow is pressed, but for
    # Emacs ansi-term sends the same sequences for normal arrow keys. Consider
    # it a normal arrow press, because that's more important.
    '\x1bOA': Keys.Up,
    '\x1bOB': Keys.Down,
    '\x1bOC': Keys.Right,
    '\x1bOD': Keys.Left,

    '\x1b[5A': Keys.ControlUp,
    '\x1b[5B': Keys.ControlDown,
    '\x1b[5C': Keys.ControlRight,
    '\x1b[5D': Keys.ControlLeft,

    '\x1bOc': Keys.ControlRight,  # rxvt
    '\x1bOd': Keys.ControlLeft,  # rxvt

    # Tmux (Win32 subsystem) sends the following scroll events.
    '\x1b[62~': Keys.ScrollUp,
    '\x1b[63~': Keys.ScrollDown,

    '\x1b[200~': Keys.BracketedPaste,  # Start of bracketed paste.

    # Meta + arrow keys. Several terminals handle this differently.
    # The following sequences are for xterm and gnome-terminal.
    #     (Iterm sends ESC followed by the normal arrow_up/down/left/right
    #     sequences, and the OSX Terminal sends ESCb and ESCf for "alt
    #     arrow_left" and "alt arrow_right." We don't handle these
    #     explicitly, in here, because would could not distinguish between
    #     pressing ESC (to go to Vi navigation mode), followed by just the
    #     'b' or 'f' key. These combinations are handled in
    #     the input processor.)
    '\x1b[1;3D': (Keys.Escape, Keys.Left),
    '\x1b[1;3C': (Keys.Escape, Keys.Right),
    '\x1b[1;3A': (Keys.Escape, Keys.Up),
    '\x1b[1;3B': (Keys.Escape, Keys.Down),

    # Option+left/right on (some?) Macs when using iTerm defaults
    # (see issue #483)
    '\x1b[1;9D': (Keys.Escape, Keys.Left),
    '\x1b[1;9C': (Keys.Escape, Keys.Right),

    # Sequences generated by numpad 5. Not sure what it means. (It doesn't
    # appear in 'infocmp'. Just ignore.
    '\x1b[E': Keys.Ignore,  # Xterm.
    '\x1b[G': Keys.Ignore,  # Linux console.
}


def _get_reverse_ansi_sequences():
    """
    Create a dictionary that maps prompt_toolkit keys back to the VT100 escape
    sequences.
    """
    result = {}

    for sequence, key in ANSI_SEQUENCES.items():
        if not isinstance(key, tuple):
            if key not in result:
                result[key] = sequence

    return result


REVERSE_ANSI_SEQUENCES = _get_reverse_ansi_sequences()
