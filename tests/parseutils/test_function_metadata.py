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


def test_function_metadata_fields_with_unnamed_variadic_arg():
    # A variadic argument can arrive with no name, so arg_names is None while
    # arg_modes is set. fields() used to raise 'NoneType is not iterable' on
    # the zip() (issue #1204); it now falls back to the function-name column.
    f = FunctionMetadata(
        'public', 'labels', None, ['text[]'], ['v'], 'hstore',
        False, False, False, False, None,
    )
    assert [(c.name, c.datatype) for c in f.fields()] == [('labels', 'hstore')]