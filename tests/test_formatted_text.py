from __future__ import unicode_literals
from prompt_toolkit.layout.formatted_text import HTML, ANSI, to_formatted_text, Template, merge_formatted_text


def test_basic_html():
    html = HTML('<i>hello</i>')
    assert to_formatted_text(html) == [('class:i', 'hello')]

    html = HTML('<i><b>hello</b></i>')
    assert to_formatted_text(html) == [('class:i,b', 'hello')]

    html = HTML('<i><b>hello</b>world<strong>test</strong></i>after')
    assert to_formatted_text(html) == [
        ('class:i,b', 'hello'),
        ('class:i', 'world'),
        ('class:i,strong', 'test'),
        ('', 'after'),
    ]

def test_html_with_fg_bg():
    html = HTML('<style bg="ansired">hello</style>')
    assert to_formatted_text(html) == [
        ('bg:ansired', 'hello'),
    ]

    html = HTML('<style bg="ansired" fg="#ff0000">hello</style>')
    assert to_formatted_text(html) == [
        ('fg:#ff0000 bg:ansired', 'hello'),
    ]

    html = HTML('<style bg="ansired" fg="#ff0000">hello <world fg="ansiblue">world</world></style>')
    assert to_formatted_text(html) == [
        ('fg:#ff0000 bg:ansired', 'hello '),
        ('class:world fg:ansiblue bg:ansired', 'world'),
    ]


def test_ansi_formatting():
    value = ANSI('\x1b[32mHe\x1b[45mllo')

    assert to_formatted_text(value) == [
        ('#ansidarkgreen', 'H'),
        ('#ansidarkgreen', 'e'),
        ('#ansidarkgreen bg:#ansipurple', 'l'),
        ('#ansidarkgreen bg:#ansipurple', 'l'),
        ('#ansidarkgreen bg:#ansipurple', 'o'),
    ]

    # Zero width escapes.
    value = ANSI('ab\001cd\002ef')

    assert to_formatted_text(value) == [
        ('', 'a'),
        ('', 'b'),
        ('[ZeroWidthEscape]', 'cd'),
        ('', 'e'),
        ('', 'f'),
    ]


def test_interpolation():
    value = Template(' {} ').format(HTML('<b>hello</b>'))

    assert to_formatted_text(value) == [
        ('', ' '),
        ('class:b', 'hello'),
        ('', ' '),
    ]

    value = Template('a{}b{}c').format(HTML('<b>hello</b>'), 'world')

    assert to_formatted_text(value) == [
        ('', 'a'),
        ('class:b', 'hello'),
        ('', 'b'),
        ('', 'world'),
        ('', 'c'),
    ]


def test_html_interpolation():
    # %-style interpolation.
    value = HTML('<b>%s</b>') % 'hello'
    assert to_formatted_text(value) == [
        ('class:b', 'hello')
    ]

    value = HTML('<b>%s</b>') % ('hello', )
    assert to_formatted_text(value) == [
        ('class:b', 'hello')
    ]

    value = HTML('<b>%s</b><u>%s</u>') % ('hello', 'world')
    assert to_formatted_text(value) == [
        ('class:b', 'hello'),
        ('class:u', 'world')
    ]

    # Format function.
    value = HTML('<b>{}</b><u>{}</u>').format('hello', 'world')
    assert to_formatted_text(value) == [
        ('class:b', 'hello'),
        ('class:u', 'world')
    ]

    value = HTML('<b>{a}</b><u>{b}</u>').format(a='hello', b='world')
    assert to_formatted_text(value) == [
        ('class:b', 'hello'),
        ('class:u', 'world')
    ]


def test_merge_formatted_text():
    html1 = HTML('<u>hello</u>')
    html2 = HTML('<b>world</b>')
    result = merge_formatted_text([html1, html2])

    assert to_formatted_text(result) == [
        ('class:u', 'hello'),
        ('class:b', 'world'),
    ]
