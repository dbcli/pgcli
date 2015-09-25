from __future__ import unicode_literals

__all__ = (
    'Key',
    'Keys',
)


class Key(object):
    def __init__(self, name):

        #: Descriptive way of writing keys in configuration files. e.g. <C-A>
        #: for ``Control-A``.
        self.name = name

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.name)


class Keys(object):
    Escape = Key('<Escape>')

    ControlA = Key('<C-A>')
    ControlB = Key('<C-B>')
    ControlC = Key('<C-C>')
    ControlD = Key('<C-D>')
    ControlE = Key('<C-E>')
    ControlF = Key('<C-F>')
    ControlG = Key('<C-G>')
    ControlH = Key('<C-H>')
    ControlI = Key('<C-I>')  # Tab
    ControlJ = Key('<C-J>')  # Enter
    ControlK = Key('<C-K>')
    ControlL = Key('<C-L>')
    ControlM = Key('<C-M>')  # Enter
    ControlN = Key('<C-N>')
    ControlO = Key('<C-O>')
    ControlP = Key('<C-P>')
    ControlQ = Key('<C-Q>')
    ControlR = Key('<C-R>')
    ControlS = Key('<C-S>')
    ControlT = Key('<C-T>')
    ControlU = Key('<C-U>')
    ControlV = Key('<C-V>')
    ControlW = Key('<C-W>')
    ControlX = Key('<C-X>')
    ControlY = Key('<C-Y>')
    ControlZ = Key('<C-Z>')

    ControlSpace       = Key('<C-Space>')
    ControlBackslash   = Key('<C-Backslash>')
    ControlSquareClose = Key('<C-SquareClose>')
    ControlCircumflex  = Key('<C-Circumflex>')
    ControlUnderscore  = Key('<C-Underscore>')
    ControlLeft        = Key('<C-Left>')
    ControlRight       = Key('<C-Right>')
    ControlUp          = Key('<C-Up>')
    ControlDown        = Key('<C-Down>')

    Up          = Key('<Up>')
    Down        = Key('<Down>')
    Right       = Key('<Right>')
    Left        = Key('<Left>')
    Home        = Key('<Home>')
    End         = Key('<End>')
    Delete      = Key('<Delete>')
    ShiftDelete = Key('<ShiftDelete>')
    PageUp      = Key('<PageUp>')
    PageDown    = Key('<PageDown>')
    BackTab     = Key('<BackTab>')  # shift + tab
    Insert      = Key('<Insert>')

    Tab         = ControlI
    Backspace   = ControlH

    F1 = Key('<F1>')
    F2 = Key('<F2>')
    F3 = Key('<F3>')
    F4 = Key('<F4>')
    F5 = Key('<F5>')
    F6 = Key('<F6>')
    F7 = Key('<F7>')
    F8 = Key('<F8>')
    F9 = Key('<F9>')
    F10 = Key('<F10>')
    F11 = Key('<F11>')
    F12 = Key('<F12>')
    F13 = Key('<F13>')
    F14 = Key('<F14>')
    F15 = Key('<F15>')
    F16 = Key('<F16>')
    F17 = Key('<F17>')
    F18 = Key('<F18>')
    F19 = Key('<F19>')
    F20 = Key('<F20>')

    # Matches any key.
    Any = Key('<Any>')

    # Special
    CPRResponse = Key('<Cursor-Position-Response>')
    Vt100MouseEvent = Key('<Vt100-Mouse-Event>')
    WindowsMouseEvent = Key('<Windows-Mouse-Event>')
