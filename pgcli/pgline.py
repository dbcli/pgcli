from prompt_toolkit.line import Line

class PGLine(Line):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    @property
    def is_multiline(self):
        """
        Dynamically determine whether we're in multiline mode.
        """

        if _multiline_exception(self.text):
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
            (text == '')               # Just a plain enter without any text
            )
