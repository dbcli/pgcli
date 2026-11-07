from pgcli.packages.parseutils.meta import ColumnMetadata, FunctionMetadata
from pgcli.pgcompleter import generate_alias


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
    # Regression test: arg_modes being truthy doesn't guarantee arg_names is
    # populated (e.g. an unnamed variadic parameter). fields() used to crash
    # with "'NoneType' object is not iterable".
    f = FunctionMetadata("s", "labels", None, ["text[]"], ["v"], "hstore", False, False, False, False, None)
    assert f.fields() == [ColumnMetadata("labels", "hstore", [])]


def test_function_metadata_fields_table_mode_with_no_arg_names():
    # Without argument names there is no output column name to offer, so the
    # function name is used and generate_alias() gets a real string.
    f = FunctionMetadata("s", "f", None, ["int4", "text"], ["t", "t"], "record", False, False, True, False, None)
    fields = f.fields()
    assert fields == [ColumnMetadata("f", "record", [])]
    assert all(generate_alias(field.name) for field in fields)


def test_function_metadata_fields_table_mode_with_arg_names():
    f = FunctionMetadata("s", "f", ["a", "b"], ["int4", "text"], ["t", "t"], "record", False, False, True, False, None)
    assert f.fields() == [ColumnMetadata("a", "int4", []), ColumnMetadata("b", "text", [])]
