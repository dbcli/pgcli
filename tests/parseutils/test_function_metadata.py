from pgcli.packages.parseutils.meta import FunctionMetadata


def test_function_metadata_eq():
    f1 = FunctionMetadata("s", "f", ["x"], ["integer"], [], "int", False, False, False, False, None)
    f2 = FunctionMetadata("s", "f", ["x"], ["integer"], [], "int", False, False, False, False, None)
    f3 = FunctionMetadata("s", "g", ["x"], ["integer"], [], "int", False, False, False, False, None)
    assert f1 == f2
    assert f1 != f3
    assert not (f1 != f2)
    assert not (f1 == f3)
    assert hash(f1) == hash(f2)
    assert hash(f1) != hash(f3)


def test_function_metadata_fields_with_variadic_and_no_arg_names():
    # Regression for issue #1204: a function with a VARIADIC argument that has
    # a type but no name (e.g. `labels(variadic text[]) RETURNS hstore`) leaves
    # arg_names as None while arg_modes is truthy. fields() must not raise
    # "'NoneType' object is not iterable".
    f = FunctionMetadata(
        "public",
        "labels",
        None,  # arg_names: variadic arg has no name
        ["text[]"],
        ["v"],  # VARIADIC
        "hstore",
        False,
        False,
        False,
        False,
        None,
    )
    # No OUT/INOUT/TABLE columns, so fields() yields nothing.
    assert f.fields() == []
