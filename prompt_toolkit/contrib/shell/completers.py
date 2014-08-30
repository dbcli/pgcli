import os

from prompt_toolkit.code import Completion

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

                    yield Completion(filename, completion)
        except OSError:
            pass
