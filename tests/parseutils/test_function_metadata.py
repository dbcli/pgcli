from pgcli.packages.parseutils.meta import FunctionMetadata


def test_function_metadata_eq():
    f1 = FunctionMetadata(
        's', 'f', ['x'], ['integer'], [], 'int', False, False, False, None
    )
    f2 = FunctionMetadata(
        's', 'f', ['x'], ['integer'], [], 'int', False, False, False, None
    )
    f3 = FunctionMetadata(
        's', 'g', ['x'], ['integer'], [], 'int', False, False, False, None
    )
    assert f1 == f2
    assert f1 != f3
    assert not (f1 != f2)
    assert not (f1 == f3)
    assert hash(f1) == hash(f2)
    assert hash(f1) != hash(f3)
