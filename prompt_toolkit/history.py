from __future__ import unicode_literals

import datetime
import os

__all__ = ('History', 'FileHistory')


class History(object):
    """
    Base ``History`` class that keeps a list of all strings in memory.
    """
    def __init__(self):
        self.strings = []

    def append(self, string):
        self.strings.append(string)

    def __getitem__(self, key):
        return self.strings[key]

    def __len__(self):
        return len(self.strings)

    def __bool__(self):
        """
        Don't evaluate to False, even when the history is empty.
        (Python calls __len__ if __bool__ is not implemented.)
        """
        return True

    __nonzero__ = __bool__  # For Python 2.


class FileHistory(History):
    """
    ``History`` class that stores all strings in a file.
    """
    def __init__(self, filename):
        super(FileHistory, self).__init__()
        self.filename = filename

        self._load()

    def _load(self):
        lines = []

        def add():
            if lines:
                # Join and drop trailing newline.
                string = ''.join(lines)[:-1]

                self.strings.append(string)

        if os.path.exists(self.filename):
            with open(self.filename, 'rb') as f:
                for line in f:
                    line = line.decode('utf-8')

                    if line.startswith('+'):
                        lines.append(line[1:])
                    else:
                        add()
                        lines = []

                add()

    def append(self, string):
        super(FileHistory, self).append(string)

        # Save to file.
        with open(self.filename, 'ab') as f:
            write = lambda t: f.write(t.encode('utf-8'))

            write('\n# %s\n' % datetime.datetime.now())
            for line in string.split('\n'):
                write('+%s\n' % line)
