from __future__ import unicode_literals, absolute_import

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.contrib.completers import WordCompleter, PathCompleter
from prompt_toolkit.document import Document

from .commands import commands_with_help

import bdb
import os
import re
import sys


class PdbCommandsCompleter(WordCompleter):
    """
    Completer for all the pdb commands.
    """
    def __init__(self, pdb):
        meta_dict = {}
        meta_dict.update(commands_with_help)

        for k, v in pdb.aliases.items():
            meta_dict[k] = 'Alias for: %s' % v

        super(PdbCommandsCompleter, self).__init__(
            list(commands_with_help.keys()) + list(pdb.aliases.keys()),
            meta_dict=meta_dict,
            ignore_case=True)


class PythonFileCompleter(Completer):
    """
    Completion on Python modules in sys.path.
    """
    def get_completions(self, document, complete_event):
        for dirname in sys.path:
            full_path = os.path.join(dirname, document.text)

            def filter(name):
                return name.endswith('.py')

            for c in PathCompleter(file_filter=filter).get_completions(
                    Document(full_path, len(full_path)), complete_event):
                yield c


class PythonFunctionCompleter(Completer):
    """
    Complete on Python functions that exist in the same file as the current
    stack frame.
    """
    def __init__(self, pdb):
        self.pdb = pdb

    def get_completions(self, document, complete_event):
        text = document.text

        # Get filename of current frame.
        filename = self.pdb.curframe.f_code.co_filename
        if filename.endswith('pyc'):
            filename = filename[:-1]

        basename = os.path.basename(filename)

        # Find functions in this file.
        with open(filename, 'r') as f:
            for i, line in enumerate(f.readlines()):
                names = re.findall('def\s+([^\s]+)\s*[(]', line)
                signature = re.findall('(def\s+[^\s]+\s*[(][^)]*[)])', line)

                for n in names:
                    if n.startswith(text):
                        if signature:
                            display_meta = '%s:%s - %s' % (basename, i, signature[0])
                        else:
                            display_meta = '%s:%s' % (basename, i)

                        yield Completion(n, -len(text), display_meta=display_meta)


class BreakPointListCompleter(WordCompleter):
    """
    Complter for breakpoint numbers.
    """
    def __init__(self, only_disabled=False, only_enabled=False):
        commands = []
        meta_dict = {}

        for bp in bdb.Breakpoint.bpbynumber:
            if bp:
                if only_disabled and bp.enabled:
                    continue
                if only_enabled and not bp.enabled:
                    continue

                commands.append('%s' % bp.number)
                meta_dict['%s' % bp.number] = '%s:%s' % (bp.file, bp.line)

        super(BreakPointListCompleter, self).__init__(
            commands,
            meta_dict=meta_dict)


class AliasCompleter(WordCompleter):
    def __init__(self, pdb):
        super(AliasCompleter, self).__init__(
            pdb.aliases.keys(),
            meta_dict=pdb.aliases)
