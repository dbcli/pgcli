from __future__ import unicode_literals
from prompt_toolkit.token import Token



def test_token():
    t1 = Token.A.B.C
    t2 = Token.A.B.C

    # Tokens are stored using this tuple notation underneath.
    assert t1 == ('A', 'B', 'C')

    # Creating the same tuple twice, should reuse the same instance.
    # (This makes comparing Tokens faster.)
    assert id(t1) == id(t2)

def test_token_or():
    t1 = Token.A.B.C
    t2 = Token.D.E.F

    t3 = t1 | t2
    t4 = t1 | t2

    # The OR operation should insert a colon.
    assert t3 == ('A', 'B', 'C', ':', 'D', 'E', 'F')

    # When applying the OR operation twice between the same
    # tuples, that should also yield the object.
    assert id(t3) == id(t4)
