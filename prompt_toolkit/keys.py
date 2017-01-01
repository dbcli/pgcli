from __future__ import unicode_literals

__all__ = (
    'Keys',
)

class Keys(object):
    Escape = 'escape'

    ControlAt = 'c-@'

    ControlA = 'c-a'
    ControlB = 'c-b'
    ControlC = 'c-c'
    ControlD = 'c-d'
    ControlE = 'c-e'
    ControlF = 'c-f'
    ControlG = 'c-g'
    ControlH = 'c-h'
    ControlI = 'c-i'  # Tab
    ControlJ = 'c-j'  # Newline
    ControlK = 'c-k'
    ControlL = 'c-l'
    ControlM = 'c-m'  # Carriage return
    ControlN = 'c-n'
    ControlO = 'c-o'
    ControlP = 'c-p'
    ControlQ = 'c-q'
    ControlR = 'c-r'
    ControlS = 'c-s'
    ControlT = 'c-t'
    ControlU = 'c-u'
    ControlV = 'c-v'
    ControlW = 'c-w'
    ControlX = 'c-x'
    ControlY = 'c-y'
    ControlZ = 'c-z'

    ControlSquareOpen  = 'c-['
    ControlBackslash   = 'c-\\'
    ControlSquareClose = 'c-]'
    ControlCircumflex  = 'c-^'
    ControlUnderscore  = 'c-_'

    ControlLeft        = 'c-left'
    ControlRight       = 'c-right'
    ControlUp          = 'c-up'
    ControlDown        = 'c-down'

    Up          = 'up'
    Down        = 'down'
    Right       = 'right'
    Left        = 'left'

    ShiftLeft   = 's-left'
    ShiftUp     = 's-up'
    ShiftDown   = 's-down'
    ShiftRight  = 's-right'
    ShiftDelete = 's-delete'
    BackTab     = 's-tab'  # shift + tab

    Home        = 'home'
    End         = 'end'
    Delete      = 'delete'
    ControlDelete = 'c-delete'
    PageUp      = 'pageup'
    PageDown    = 'pagedown'
    Insert      = 'insert'
    Backspace   = 'backspace'

    F1 = 'f1'
    F2 = 'f2'
    F3 = 'f3'
    F4 = 'f4'
    F5 = 'f5'
    F6 = 'f6'
    F7 = 'f7'
    F8 = 'f8'
    F9 = 'f9'
    F10 = 'f10'
    F11 = 'f11'
    F12 = 'f12'
    F13 = 'f13'
    F14 = 'f14'
    F15 = 'f15'
    F16 = 'f16'
    F17 = 'f17'
    F18 = 'f18'
    F19 = 'f19'
    F20 = 'f20'
    F21 = 'f21'
    F22 = 'f22'
    F23 = 'f23'
    F24 = 'f24'

    # Matches any key.
    Any = '<Any>'

    # Special3
    ScrollUp    = '<ScrollUp>'
    ScrollDown  = '<ScrollDown>'

    CPRResponse = '<Cursor-Position-Response>'
    Vt100MouseEvent = '<Vt100-Mouse-Event>'
    WindowsMouseEvent = '<Windows-Mouse-Event>'
    BracketedPaste = '<Bracketed-Paste>'

    # For internal use: key which is ignored.
    # (The key binding for this key should not do anything.)
    Ignore = '<Ignore>'

    # Aliases.
    ControlSpace = ControlAt
    Tab          = ControlI
    Enter        = ControlM
