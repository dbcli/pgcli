from __future__ import unicode_literals
from prompt_toolkit.filters import Condition, Never, Always, Filter
from prompt_toolkit.filters.types import CLIFilter, SimpleFilter
from prompt_toolkit.filters.utils import to_cli_filter, to_simple_filter
from prompt_toolkit.filters.cli import HasArg, HasFocus, HasSelection

import pytest


def test_condition_filter_args():
    c = Condition(lambda a, b, c: True)
    assert c.test_args('a', 'b', 'c')
    assert not c.test_args()
    assert not c.test_args('a')
    assert not c.test_args('a', 'b')
    assert not c.test_args('a', 'b', 'c', 'd')

    c2 = Condition(lambda a, b=1: True)
    assert c2.test_args('a')
    assert c2.test_args('a', 'b')
    assert not c2.test_args('a', 'b', 'c')
    assert not c2.test_args()

    c3 = Condition(lambda *a: True)
    assert c3.test_args()
    assert c3.test_args('a')
    assert c3.test_args('a', 'b')


def test_and_arg():
    c1 = Condition(lambda a: True)
    c2 = Condition(lambda a: True)
    c3 = c1 & c2

    assert c3.test_args('a')
    assert not c3.test_args()
    assert not c3.test_args('a', 'b')


def test_or_arg():
    c1 = Condition(lambda a: True)
    c2 = Condition(lambda a: True)
    c3 = c1 | c2

    assert c3.test_args('a')
    assert not c3.test_args()
    assert not c3.test_args('a', 'b')


def test_condition():
    c = Condition(lambda a: a % 2 == 0)
    assert c(4)
    assert c(6)
    assert not c(5)
    assert not c(3)


def test_never():
    assert not Never()()


def test_always():
    assert Always()()


def test_invert():
    assert not (~Always())()
    assert (~Never()())

    c = ~Condition(lambda: False)
    assert c()


def test_or():
    for a in (True, False):
        for b in (True, False):
            c1 = Condition(lambda: a)
            c2 = Condition(lambda: b)
            c3 = c1 | c2

            assert isinstance(c3, Filter)
            assert c3() == a or b


def test_and():
    for a in (True, False):
        for b in (True, False):
            c1 = Condition(lambda: a)
            c2 = Condition(lambda: b)
            c3 = c1 & c2

            assert isinstance(c3, Filter)
            assert c3() == (a and b)


def test_cli_filter():
    c1 = Condition(lambda cli: True)
    assert isinstance(c1, CLIFilter)
    assert not isinstance(c1, SimpleFilter)

    c2 = Condition(lambda: True)
    assert not isinstance(c2, CLIFilter)
    assert isinstance(c2, SimpleFilter)

    c3 = c1 | c2
    assert not isinstance(c3, CLIFilter)
    assert not isinstance(c3, SimpleFilter)

    c4 = Condition(lambda cli: True)
    c5 = Condition(lambda cli: True)
    c6 = c4 & c5
    c7 = c4 | c5
    assert isinstance(c6, CLIFilter)
    assert isinstance(c7, CLIFilter)
    assert not isinstance(c6, SimpleFilter)
    assert not isinstance(c7, SimpleFilter)

    c8 = Condition(lambda *args: True)
    assert isinstance(c8, CLIFilter)
    assert isinstance(c8, SimpleFilter)


def test_to_cli_filter():
    f1 = to_cli_filter(True)
    f2 = to_cli_filter(False)
    f3 = to_cli_filter(Condition(lambda cli: True))
    f4 = to_cli_filter(Condition(lambda cli: False))

    assert isinstance(f1, CLIFilter)
    assert isinstance(f2, CLIFilter)
    assert isinstance(f3, CLIFilter)
    assert isinstance(f4, CLIFilter)
    assert f1(None)
    assert not f2(None)
    assert f3(None)
    assert not f4(None)

    with pytest.raises(TypeError):
        to_cli_filter(4)
    with pytest.raises(TypeError):
        to_cli_filter(Condition(lambda: True))


def test_to_simple_filter():
    f1 = to_simple_filter(True)
    f2 = to_simple_filter(False)
    f3 = to_simple_filter(Condition(lambda: True))
    f4 = to_simple_filter(Condition(lambda: False))

    assert isinstance(f1, SimpleFilter)
    assert isinstance(f2, SimpleFilter)
    assert isinstance(f3, SimpleFilter)
    assert isinstance(f4, SimpleFilter)
    assert f1()
    assert not f2()
    assert f3()
    assert not f4()

    with pytest.raises(TypeError):
        to_simple_filter(4)
    with pytest.raises(TypeError):
        to_simple_filter(Condition(lambda cli: True))


def test_cli_filters():
    assert isinstance(HasArg(), CLIFilter)
    assert isinstance(HasFocus('BUFFER_NAME'), CLIFilter)
    assert isinstance(HasSelection(), CLIFilter)
