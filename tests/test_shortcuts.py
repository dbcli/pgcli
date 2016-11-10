from prompt_toolkit.shortcuts import _split_multiline_prompt
from prompt_toolkit.token import Token


def test_split_multiline_prompt():
    # Test 1: no newlines:
    tokens = [(Token, 'ab')]
    has_before_tokens, before, first_input_line = _split_multiline_prompt(lambda cli: tokens)
    assert has_before_tokens(None) is False
    assert before(None) == []
    assert first_input_line(None) == [
        (Token, 'a'),
        (Token, 'b'),
    ]

    # Test 1: multiple lines.
    tokens = [(Token, 'ab\ncd\nef')]
    has_before_tokens, before, first_input_line = _split_multiline_prompt(lambda cli: tokens)
    assert has_before_tokens(None) is True
    assert before(None) == [
        (Token, 'a'),
        (Token, 'b'),
        (Token, '\n'),
        (Token, 'c'),
        (Token, 'd'),
    ]
    assert first_input_line(None) == [
        (Token, 'e'),
        (Token, 'f'),
    ]

    # Edge case 1: starting with a newline.
    tokens = [(Token, '\nab')]
    has_before_tokens, before, first_input_line = _split_multiline_prompt(lambda cli: tokens)
    assert has_before_tokens(None) is True
    assert before(None) == []
    assert first_input_line(None) == [
        (Token, 'a'),
        (Token, 'b')
    ]

    # Edge case 2: starting with two newlines.
    tokens = [(Token, '\n\nab')]
    has_before_tokens, before, first_input_line = _split_multiline_prompt(lambda cli: tokens)
    assert has_before_tokens(None) is True
    assert before(None) == [(Token, '\n')]
    assert first_input_line(None) == [
        (Token, 'a'),
        (Token, 'b')
    ]
