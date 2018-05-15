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
        self.macro = []
        self.current_recording = None

    def reset(self):
        self.current_recording = None

    @property
    def is_recording(self):
        " Tell whether we are recording a macro. "
        return self.current_recording is not None

    def start_macro(self):
        " Start recording macro. "
        self.current_recording = []

    def end_macro(self):
        " End recording macro. "
        self.macro = self.current_recording
        self.current_recording = None
