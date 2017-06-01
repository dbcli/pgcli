from __future__ import unicode_literals
from prompt_toolkit.filters import Condition, Never, Always, Filter, to_filter
import pytest


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


def test_to_filter():
    f1 = to_filter(True)
    f2 = to_filter(False)
    f3 = to_filter(Condition(lambda: True))
    f4 = to_filter(Condition(lambda: False))

    assert isinstance(f1, Filter)
    assert isinstance(f2, Filter)
    assert isinstance(f3, Filter)
    assert isinstance(f4, Filter)
    assert f1()
    assert not f2()
    assert f3()
    assert not f4()

    with pytest.raises(TypeError):
        to_filter(4)
