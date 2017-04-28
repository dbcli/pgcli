"""
Test `shortcuts.print_formatted_text`.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import print_formatted_text
from prompt_toolkit.styles import Style


class _Capture:
    " Emulate an stdout object. "
    encoding = 'utf-8'

    def __init__(self):
        self._data = []

    def write(self, data):
        self._data.append(data)

    @property
    def data(self):
        return b''.join(self._data)

    def flush(self):
        pass

    def isatty(self):
        return True


def test_print_formatted_text():
    f = _Capture()
    print_formatted_text([('', 'hello'), ('', 'world')], file=f)
    assert b'hello' in f.data
    assert b'world' in f.data


def test_with_style():
    f = _Capture()
    style = Style.from_dict({
        'hello': '#ff0066',
        'world': '#44ff44 italic',
    })
    tokens = [
        ('class:hello', 'Hello '),
        ('class:world', 'world'),
    ]
    print_formatted_text(tokens, style=style, file=f)
    assert b'\x1b[0;38;5;197mHello' in f.data
    assert b'\x1b[0;38;5;83;3mworld' in f.data
