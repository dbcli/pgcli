from pgcli.packages.parseutils.meta import ColumnMetadata, FunctionMetadata


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
    # Issue #1204: labels(variadic text[]) RETURNS hstore has arg_modes but no arg_names.
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
    # No OUT/INOUT/TABLE columns, so the function name is the output column.
    assert f.fields() == [ColumnMetadata("labels", "hstore", [])]
