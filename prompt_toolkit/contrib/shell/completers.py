from __future__ import unicode_literals
import os

from prompt_toolkit.completion import Completion


class Path(object):
    """
    Complete for Path variables.
    """
    _include_files = True

    def complete(self, text):
        try:
            directory = os.path.dirname(text) or '.'
            prefix = os.path.basename(text)

            for filename in os.listdir(directory):
                if filename.startswith(prefix):
                    completion = filename[len(prefix):]

                    if os.path.isdir(os.path.join(directory, filename)):
                        completion += '/'
                    else:
                        if not self._include_files:
                            continue

                    yield Completion(completion, 0, display=filename)
        except OSError:
            pass


class Directory(Path):
    _include_files = False


class ExecutableInPATH(object):
    """
    Complete on the names of all the executables that are found in the PATH
    environment variable.
    """
    def complete(self, text):
        paths = os.environ.get('PATH', '').split(':')

        for p in paths:
            if os.path.isdir(p):
                for filename in os.listdir(p):
                    if filename.startswith(text):
                        if os.access(os.path.join(p, filename), os.X_OK):
                            yield Completion(filename, -len(text))
