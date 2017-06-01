from prompt_toolkit.shortcuts.prompt import _split_multiline_prompt


def test_split_multiline_prompt():
    # Test 1: no newlines:
    tokens = [('class:testclass', 'ab')]
    has_before_tokens, before, first_input_line = _split_multiline_prompt(lambda: tokens)
    assert has_before_tokens() is False
    assert before() == []
    assert first_input_line() == [
        ('class:testclass', 'a'),
        ('class:testclass', 'b'),
    ]

    # Test 1: multiple lines.
    tokens = [('class:testclass', 'ab\ncd\nef')]
    has_before_tokens, before, first_input_line = _split_multiline_prompt(lambda: tokens)
    assert has_before_tokens() is True
    assert before() == [
        ('class:testclass', 'a'),
        ('class:testclass', 'b'),
        ('class:testclass', '\n'),
        ('class:testclass', 'c'),
        ('class:testclass', 'd'),
    ]
    assert first_input_line() == [
        ('class:testclass', 'e'),
        ('class:testclass', 'f'),
    ]

    # Edge case 1: starting with a newline.
    tokens = [('class:testclass', '\nab')]
    has_before_tokens, before, first_input_line = _split_multiline_prompt(lambda: tokens)
    assert has_before_tokens() is True
    assert before() == []
    assert first_input_line() == [
        ('class:testclass', 'a'),
        ('class:testclass', 'b')
    ]

    # Edge case 2: starting with two newlines.
    tokens = [('class:testclass', '\n\nab')]
    has_before_tokens, before, first_input_line = _split_multiline_prompt(lambda: tokens)
    assert has_before_tokens() is True
    assert before() == [('class:testclass', '\n')]
    assert first_input_line() == [
        ('class:testclass', 'a'),
        ('class:testclass', 'b')
    ]
