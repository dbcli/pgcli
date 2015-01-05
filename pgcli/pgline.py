from prompt_toolkit.line import Line

class PGLine(Line):
    def __init__(self, always_multiline, *args, **kwargs):
        self.always_multiline = always_multiline
        super(self.__class__, self).__init__(*args, **kwargs)

    @property
    def is_multiline(self):
        """
        Dynamically determine whether we're in multiline mode.
        """
        if not self.always_multiline:
            return False

        if self.always_multiline and _multiline_exception(self.text):
            return False

        return True

    @is_multiline.setter
    def is_multiline(self, value):
        pass

def _multiline_exception(text):
    text = text.strip()
    return (text.startswith('\\') or   # Special Command
            text.endswith(';') or      # Ended with a semi-colon
            (text == 'exit') or        # Exit doesn't need semi-colon
            (text == 'quit') or        # Quit doesn't need semi-colon
            (text == ':q') or          # To all the vim fans out there
            (text == '')               # Just a plain enter without any text
            )
