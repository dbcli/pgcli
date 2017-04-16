from __future__ import unicode_literals

from prompt_toolkit.styles import Attrs, Style
from collections import OrderedDict


def test_style_from_dict():
    style = Style.from_dict({
        'a': '#ff0000 bold underline italic',
        'b': 'bg:#00ff00 blink reverse',
    })

    # Lookup of class:a.
    expected = Attrs(color='ff0000', bgcolor='', bold=True,
                     underline=True, italic=True, blink=False, reverse=False)
    assert style.get_attrs_for_style_str('class:a') == expected

    # Lookup of class:b.
    expected = Attrs(color='', bgcolor='00ff00', bold=False,
                     underline=False, italic=False, blink=True, reverse=True)
    assert style.get_attrs_for_style_str('class:b') == expected

    # Test inline style.
    expected = Attrs(color='ff0000', bgcolor='', bold=False,
                     underline=False, italic=False, blink=False, reverse=False)
    assert style.get_attrs_for_style_str('#ff0000') == expected

    # Combine class name and inline style (inline attributes always get priority.)
    expected = Attrs(color='00ff00', bgcolor='', bold=True,
                     underline=True, italic=True, blink=False, reverse=False)
    assert style.get_attrs_for_style_str('class:a #00ff00') == expected

    expected = Attrs(color='00ff00', bgcolor='', bold=True,
                     underline=True, italic=True, blink=False, reverse=False)
    assert style.get_attrs_for_style_str('#00ff00 class:a') == expected


def test_class_combinations_1():
    # In this case, our style has both class 'a' and 'b'.
    # Given that the style for 'a b' is defined at the end, that one is used.
    style = Style.from_dict(OrderedDict([
        ('a', '#0000ff'),
        ('b', '#00ff00'),
        ('a b', '#ff0000'),
    ]))
    expected = Attrs(color='ff0000', bgcolor='', bold=False,
                     underline=False, italic=False, blink=False, reverse=False)
    assert style.get_attrs_for_style_str('class:a class:b') == expected


def test_class_combinations_2():
    # In this case, our style has both class 'a' and 'b', but the style for 'a'
    # is defined at the end. Because of that, this gets priority.
    style = Style.from_dict(OrderedDict([
        ('a b', '#ff0000'),
        ('b', '#00ff00'),
        ('a', '#0000ff'),
    ]))
    expected = Attrs(color='0000ff', bgcolor='', bold=False,
                     underline=False, italic=False, blink=False, reverse=False)
    assert style.get_attrs_for_style_str('class:a class:b') == expected
