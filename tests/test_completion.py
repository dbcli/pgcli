from __future__ import unicode_literals, absolute_import, print_function

import os
import shutil
import tempfile

from contextlib import contextmanager
from six import text_type

from prompt_toolkit.completion import CompleteEvent, PathCompleter, WordCompleter
from prompt_toolkit.document import Document


@contextmanager
def chdir(directory):
    """Context manager for current working directory temporary change."""
    orig_dir = os.getcwd()
    os.chdir(directory)

    try:
        yield
    finally:
        os.chdir(orig_dir)


def write_test_files(test_dir, names=None):
    """Write test files in test_dir using the names list."""
    names = names or range(10)
    for i in names:
        with open(os.path.join(test_dir, str(i)), 'wb') as out:
            out.write(''.encode('UTF-8'))


def test_pathcompleter_completes_in_current_directory():
    completer = PathCompleter()
    doc_text = ''
    doc = Document(doc_text, len(doc_text))
    event = CompleteEvent()
    completions = list(completer.get_completions(doc, event))
    assert len(completions) > 0


def test_pathcompleter_completes_files_in_current_directory():
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
        assert expected == result

    # cleanup
    shutil.rmtree(test_dir)


def test_pathcompleter_completes_files_in_absolute_directory():
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
    assert expected == result

    # cleanup
    shutil.rmtree(test_dir)


def test_pathcompleter_completes_directories_with_only_directories():
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
        assert ['subdir'] == result

    # check that there is no completion when passing a file
    with chdir(test_dir):
        completer = PathCompleter(only_directories=True)
        doc_text = '1'
        doc = Document(doc_text, len(doc_text))
        event = CompleteEvent()
        completions = list(completer.get_completions(doc, event))
        assert [] == completions

    # cleanup
    shutil.rmtree(test_dir)


def test_pathcompleter_respects_completions_under_min_input_len():
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
        assert [] == completions

    # min len:1 and text of len 1
    with chdir(test_dir):
        completer = PathCompleter(min_input_len=1)
        doc_text = '1'
        doc = Document(doc_text, len(doc_text))
        event = CompleteEvent()
        completions = list(completer.get_completions(doc, event))
        result = [c.text for c in completions]
        assert [''] == result

    # min len:0 and text of len 2
    with chdir(test_dir):
        completer = PathCompleter(min_input_len=0)
        doc_text = '1'
        doc = Document(doc_text, len(doc_text))
        event = CompleteEvent()
        completions = list(completer.get_completions(doc, event))
        result = [c.text for c in completions]
        assert [''] == result

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
        assert ['', '2'] == result

    # min len:2 and text of len 1
    with chdir(test_dir):
        completer = PathCompleter(min_input_len=2)
        doc_text = '2'
        doc = Document(doc_text, len(doc_text))
        event = CompleteEvent()
        completions = list(completer.get_completions(doc, event))
        assert [] == completions

    # cleanup
    shutil.rmtree(test_dir)


def test_pathcompleter_does_not_expanduser_by_default():
    completer = PathCompleter()
    doc_text = '~'
    doc = Document(doc_text, len(doc_text))
    event = CompleteEvent()
    completions = list(completer.get_completions(doc, event))
    assert [] == completions


def test_pathcompleter_can_expanduser():
    completer = PathCompleter(expanduser=True)
    doc_text = '~'
    doc = Document(doc_text, len(doc_text))
    event = CompleteEvent()
    completions = list(completer.get_completions(doc, event))
    assert len(completions) > 0


def test_pathcompleter_can_apply_file_filter():
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
        assert ['my.csv'] == result

    # cleanup
    shutil.rmtree(test_dir)


def test_pathcompleter_get_paths_constrains_path():
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
        assert expected == result

    # cleanup
    shutil.rmtree(test_dir)


def test_word_completer_static_word_list():
    completer = WordCompleter(['abc', 'def', 'aaa'])

    # Static list on empty input.
    completions = completer.get_completions(Document(''), CompleteEvent())
    assert [c.text for c in completions] == ['abc', 'def', 'aaa']

    # Static list on non-empty input.
    completions = completer.get_completions(Document('a'), CompleteEvent())
    assert [c.text for c in completions] == ['abc', 'aaa']

    completions = completer.get_completions(Document('A'), CompleteEvent())
    assert [c.text for c in completions] == []

    # Multiple words. (Check last only.)
    completions = completer.get_completions(Document('test a'), CompleteEvent())
    assert [c.text for c in completions] == ['abc', 'aaa']


def test_word_completer_ignore_case():
    completer = WordCompleter(['abc', 'def', 'aaa'], ignore_case=True)
    completions = completer.get_completions(Document('a'), CompleteEvent())
    assert [c.text for c in completions] == ['abc', 'aaa']

    completions = completer.get_completions(Document('A'), CompleteEvent())
    assert [c.text for c in completions] == ['abc', 'aaa']


def test_word_completer_match_middle():
    completer = WordCompleter(['abc', 'def', 'abca'], match_middle=True)
    completions = completer.get_completions(Document('bc'), CompleteEvent())
    assert [c.text for c in completions] == ['abc', 'abca']


def test_word_completer_sentence():
    # With sentence=True
    completer = WordCompleter(['hello world', 'www', 'hello www', 'hello there'], sentence=True)
    completions = completer.get_completions(Document('hello w'), CompleteEvent())
    assert [c.text for c in completions] == ['hello world', 'hello www']

    # With sentence=False
    completer = WordCompleter(['hello world', 'www', 'hello www', 'hello there'], sentence=False)
    completions = completer.get_completions(Document('hello w'), CompleteEvent())
    assert [c.text for c in completions] == ['www']


def test_word_completer_dynamic_word_list():
    called = [0]
    def get_words():
        called[0] += 1
        return ['abc', 'def', 'aaa']

    completer = WordCompleter(get_words)

    # Dynamic list on empty input.
    completions = completer.get_completions(Document(''), CompleteEvent())
    assert [c.text for c in completions] == ['abc', 'def', 'aaa']
    assert called[0] == 1

    # Static list on non-empty input.
    completions = completer.get_completions(Document('a'), CompleteEvent())
    assert [c.text for c in completions] == ['abc', 'aaa']
    assert called[0] == 2
