from __future__ import unicode_literals

__all__ = [
    'InputMode',
    'CharacterFind',
    'ViState',
]


class InputMode(object):
    INSERT = 'vi-insert'
    INSERT_MULTIPLE = 'vi-insert-multiple'
    NAVIGATION = 'vi-navigation'
    REPLACE = 'vi-replace'


class CharacterFind(object):
    def __init__(self, character, backwards=False):
        self.character = character
        self.backwards = backwards


class ViState(object):
    """
    Mutable class to hold the state of the Vi navigation.
    """
    def __init__(self):
        #: None or CharacterFind instance. (This is used to repeat the last
        #: search in Vi mode, by pressing the 'n' or 'N' in navigation mode.)
        self.last_character_find = None

        # When an operator is given and we are waiting for text object,
        # -- e.g. in the case of 'dw', after the 'd' --, an operator callback
        # is set here.
        self.operator_func = None
        self.operator_arg = None

        #: Named registers. Maps register name (e.g. 'a') to
        #: :class:`ClipboardData` instances.
        self.named_registers = {}

        #: The Vi mode we're currently in to.
        self.__input_mode = InputMode.INSERT

        #: Waiting for digraph.
        self.waiting_for_digraph = False
        self.digraph_symbol1 = None  # (None or a symbol.)

        #: When true, make ~ act as an operator.
        self.tilde_operator = False

        #: Register in which we are recording a macro.
        #: `None` when not recording anything.
        # Note that the recording is only stored in the register after the
        # recording is stopped. So we record in a seperate `current_recording`
        # variable.
        self.recording_register = None
        self.current_recording = ''

    @property
    def input_mode(self):
        " Get `InputMode`. "
        return self.__input_mode

    @input_mode.setter
    def input_mode(self, value):
        " Set `InputMode`. "
        if value == InputMode.NAVIGATION:
            self.waiting_for_digraph = False
            self.operator_func = None
            self.operator_arg = None

        self.__input_mode = value

    def reset(self):
        """
        Reset state, go back to the given mode. INSERT by default.
        """
        # Go back to insert mode.
        self.input_mode = InputMode.INSERT

        self.waiting_for_digraph = False
        self.operator_func = None
        self.operator_arg = None

        # Reset recording state.
        self.recording_register = None
        self.current_recording = ''
