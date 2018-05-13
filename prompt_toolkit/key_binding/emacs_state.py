from __future__ import unicode_literals

__all__ = [
    'EmacsState',
]


class EmacsState(object):
    """
    Mutable class to hold Emacs specific state.
    """
    def __init__(self):
        # Simple macro recording. (Like Readline does.)
        # (For Emacs mode.)
        self.record_macro = False
        self.macro = []

    def reset(self):
        self.record_macro = False
        self.macro = []

    def start_macro(self):
        " Start recording macro. "
        self.record_macro = True
        self.macro = []

    def end_macro(self):
        " End recording macro. "
        self.record_macro = False
