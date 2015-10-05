from __future__ import unicode_literals
from __future__ import absolute_import
from __future__ import print_function

import os
import shutil
import tempfile
import unittest

from six import text_type

from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.contrib.completers.filesystem import PathCompleter


class chdir(object):
    """Context manager for current working directory temporary change."""
    def __init__(self, directory):
        self.new_dir = directory
        self.orig_dir = os.getcwd()

    def __enter__(self):
        os.chdir(self.new_dir)

    def __exit__(self, *args):
        os.chdir(self.orig_dir)


def write_test_files(test_dir, names=None):
    """Write test files in test_dir using the names list."""
    names = names or range(10)
    for i in names:
        with open(os.path.join(test_dir, str(i)), 'wb') as out:
            out.write(''.encode('UTF-8'))


class PathCompleterTest(unittest.TestCase):

    def test_pathcompleter_completes_in_current_directory(self):
        completer = PathCompleter()
        doc_text = ''
        doc = Document(doc_text, len(doc_text))
        event = CompleteEvent()
        completions = list(completer.get_completions(doc, event))
        self.assertTrue(len(completions) > 0)

    def test_pathcompleter_completes_files_in_current_directory(self):
        # setup: create a test dir with 10 files
        test_dir = tempfile.mkdtemp()
        write_test_files(test_dir)

        expected = sorted([str(i) for i in range(10)])

        if not test_dir.endswith(os.path.sep):
            test_dir += os.path.sep

        with chdir(test_dir):
            completer = PathCompleter()
            # this should complete on the cwd
            doc_text = ''
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            result = sorted(c.text for c in completions)
            self.assertEqual(expected, result)

        # cleanup
        shutil.rmtree(test_dir)

    def test_pathcompleter_completes_files_in_absolute_directory(self):
        # setup: create a test dir with 10 files
        test_dir = tempfile.mkdtemp()
        write_test_files(test_dir)

        expected = sorted([str(i) for i in range(10)])

        test_dir = os.path.abspath(test_dir)
        if not test_dir.endswith(os.path.sep):
            test_dir += os.path.sep
        
        completer = PathCompleter()
        # force unicode
        doc_text = text_type(test_dir)
        doc = Document(doc_text, len(doc_text))
        event = CompleteEvent()
        completions = list(completer.get_completions(doc, event))
        result = sorted([c.text for c in completions])
        self.assertEqual(expected, result)

        # cleanup
        shutil.rmtree(test_dir)

    def test_pathcompleter_completes_directories_with_only_directories(self):
        # setup: create a test dir with 10 files
        test_dir = tempfile.mkdtemp()
        write_test_files(test_dir)

        # create a sub directory there
        os.mkdir(os.path.join(test_dir, 'subdir'))

        if not test_dir.endswith(os.path.sep):
            test_dir += os.path.sep

        with chdir(test_dir):
            completer = PathCompleter(only_directories=True)
            doc_text = ''
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            result = [c.text for c in completions]
            self.assertEqual(['subdir'], result)

        # check that there is no completion when passing a file
        with chdir(test_dir):
            completer = PathCompleter(only_directories=True)
            doc_text = '1'
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            self.assertEqual([], completions)

        # cleanup
        shutil.rmtree(test_dir)

    def test_pathcompleter_respects_completions_under_min_input_len(self):
        # setup: create a test dir with 10 files
        test_dir = tempfile.mkdtemp()
        write_test_files(test_dir)

        # min len:1 and no text
        with chdir(test_dir):
            completer = PathCompleter(min_input_len=1)
            doc_text = ''
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            self.assertEqual([], completions)

        # min len:1 and text of len 1
        with chdir(test_dir):
            completer = PathCompleter(min_input_len=1)
            doc_text = '1'
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            result = [c.text for c in completions]
            self.assertEqual([''], result)

        # min len:0 and text of len 2
        with chdir(test_dir):
            completer = PathCompleter(min_input_len=0)
            doc_text = '1'
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            result = [c.text for c in completions]
            self.assertEqual([''], result)

        # create 10 files with a 2 char long name
        for i in range(10):
            with open(os.path.join(test_dir, str(i) * 2), 'wb') as out:
                out.write(b'')

        # min len:1 and text of len 1
        with chdir(test_dir):
            completer = PathCompleter(min_input_len=1)
            doc_text = '2'
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            result = sorted(c.text for c in completions)
            self.assertEqual(['', '2'], result)

        # min len:2 and text of len 1
        with chdir(test_dir):
            completer = PathCompleter(min_input_len=2)
            doc_text = '2'
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            self.assertEqual([], completions)

        # cleanup
        shutil.rmtree(test_dir)

    def test_pathcompleter_does_not_expanduser_by_default(self):
        completer = PathCompleter()
        doc_text = '~'
        doc = Document(doc_text, len(doc_text))
        event = CompleteEvent()
        completions = list(completer.get_completions(doc, event))
        self.assertEqual([], completions)

    def test_pathcompleter_can_expanduser(self):
        completer = PathCompleter(expanduser=True)
        doc_text = '~'
        doc = Document(doc_text, len(doc_text))
        event = CompleteEvent()
        completions = list(completer.get_completions(doc, event))
        self.assertTrue(len(completions) > 0)

    def test_pathcompleter_can_apply_file_filter(self):
        # setup: create a test dir with 10 files
        test_dir = tempfile.mkdtemp()
        write_test_files(test_dir)

        # add a .csv file
        with open(os.path.join(test_dir, 'my.csv'), 'wb') as out:
            out.write(b'')

        file_filter = lambda f: f and f.endswith('.csv')

        with chdir(test_dir):
            completer = PathCompleter(file_filter=file_filter)
            doc_text = ''
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            result = [c.text for c in completions]
            self.assertEqual(['my.csv'], result)

        # cleanup
        shutil.rmtree(test_dir)

    def test_pathcompleter_get_paths_constrains_path(self):
        # setup: create a test dir with 10 files
        test_dir = tempfile.mkdtemp()
        write_test_files(test_dir)

        # add a subdir with 10 other files with different names
        subdir = os.path.join(test_dir, 'subdir')
        os.mkdir(subdir)
        write_test_files(subdir, 'abcdefghij')

        get_paths = lambda: ['subdir']

        with chdir(test_dir):
            completer = PathCompleter(get_paths=get_paths)
            doc_text = ''
            doc = Document(doc_text, len(doc_text))
            event = CompleteEvent()
            completions = list(completer.get_completions(doc, event))
            result = [c.text for c in completions]
            expected = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
            self.assertEqual(expected, result)

        # cleanup
        shutil.rmtree(test_dir)
