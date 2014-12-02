from prompt_toolkit.line import Line

class PGLine(Line):
    def __init__(self, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

    @property
    def is_multiline(self):
        """
        Dynamically determine whether we're in multiline mode.
        """

        if self.text.rstrip().endswith(';'):
            return False

        return True

    @is_multiline.setter
    def is_multiline(self, value):
        pass
