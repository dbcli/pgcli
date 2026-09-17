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
    # Regression test: arg_modes being truthy doesn't guarantee arg_names is
    # populated (e.g. an unnamed variadic parameter). fields() used to crash
    # with "'NoneType' object is not iterable" instead of returning [].
    f = FunctionMetadata("s", "labels", None, ["text[]"], ["v"], "hstore", False, False, False, False, None)
    assert f.fields() == []


def test_function_metadata_fields_table_mode_with_no_arg_names():
    f = FunctionMetadata("s", "f", None, ["int4", "text"], ["t", "t"], "record", False, False, True, False, None)
    fields = f.fields()
    assert len(fields) == 2
    assert [field.datatype for field in fields] == ["int4", "text"]
    assert [field.name for field in fields] == [None, None]
