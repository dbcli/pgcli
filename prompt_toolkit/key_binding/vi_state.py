from __future__ import unicode_literals

__all__ = (
    'InputMode',
    'CharacterFind',
    'ViState',
)


class InputMode(object):
    INSERT = 'vi-insert'
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

        #: The Vi mode we're currently in to.
        self.input_mode = InputMode.INSERT

    def reset(self):
        # Go back to insert mode.
        self.input_mode = InputMode.INSERT
