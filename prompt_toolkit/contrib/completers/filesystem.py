from __future__ import unicode_literals

from prompt_toolkit.completion import Completer, Completion
import os

__all__ = (
    'PathCompleter',
)


class PathCompleter(Completer):
    """
    Complete for Path variables.

    :param get_paths: Callable which returns a list of directories to look into
                      when the user enters a relative path.
    :param file_filter: Callable which takes a filename and returns whether
                        this file should show up in the completion. ``None``
                        when no filtering has to be done.
    """
    def __init__(self, include_files=True, get_paths=None, file_filter=None):   # TODO: rename include_files to only_directories.
        assert get_paths is None or callable(get_paths)
        assert file_filter is None or callable(file_filter)

        self.include_files = include_files
        self.get_paths = get_paths or (lambda: ['.'])
        self.file_filter = file_filter or (lambda _: True)

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        try:
            dirname = os.path.dirname(text)
            directories = [os.path.dirname(text)] if dirname else self.get_paths()
            prefix = os.path.basename(text)

            # Get all filenames.
            filenames = []
            for directory in directories:
                for filename in os.listdir(directory):
                    if filename.startswith(prefix):
                        filenames.append((directory, filename))

            # Sort
            filenames = sorted(filenames, key=lambda k: k[1])

            # Yield them.
            for directory, filename in filenames:
                completion = filename[len(prefix):]
                full_name = os.path.join(directory, filename)

                if not os.path.isdir(full_name):
                    if not self.include_files or not self.file_filter(full_name):
                        continue

                meta = self._get_meta(full_name)
                yield Completion(completion, 0, display=filename, display_meta=meta)
        except OSError:
            pass

    def _get_meta(self, full_name):
        """
        Return meta display string for file/directory.
        """
        if os.path.isdir(full_name):
            return 'Directory'
        elif os.path.isfile(full_name):
            return 'File'
        elif os.path.islink(full_name):
            return 'Link'
        else:
            return ''
