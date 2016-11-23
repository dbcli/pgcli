"""
Test `shortcuts.print_tokens`.
"""
from __future__ import unicode_literals
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.token import Token
from prompt_toolkit.styles import style_from_dict


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


def test_print_tokens():
    f = _Capture()
    print_tokens([(Token, 'hello'), (Token, 'world')], file=f)
    assert b'hello' in f.data
    assert b'world' in f.data


def test_with_style():
    f = _Capture()
    style = style_from_dict({
        Token.Hello: '#ff0066',
        Token.World: '#44ff44 italic',
    })
    tokens = [
        (Token.Hello, 'Hello '),
        (Token.World, 'world'),
    ]
    print_tokens(tokens, style=style, file=f)
    assert b'\x1b[0;38;5;197mHello' in f.data
    assert b'\x1b[0;38;5;83;3mworld' in f.data
