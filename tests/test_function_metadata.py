import sqlparse
from pgcli.packages.function_metadata import (
    FunctionMetadata, parse_typed_field_list, field_names)


def test_function_metadata_eq():
    f1 = FunctionMetadata('s', 'f', 'x int', 'int', False, False, False)
    f2 = FunctionMetadata('s', 'f', 'x int', 'int', False, False, False)
    f3 = FunctionMetadata('s', 'g', 'x int', 'int', False, False, False)
    assert f1 == f2
    assert f1 != f3
    assert not (f1 != f2)
    assert not (f1 == f3)
    assert hash(f1) == hash(f2)
    assert hash(f1) != hash(f3)

def test_parse_typed_field_list_simple():
    sql = 'a int, b int[][], c double precision, d text'
    tokens = sqlparse.parse(sql)[0].flatten()
    args = list(parse_typed_field_list(tokens))
    assert [arg.name for arg in args] == ['a', 'b', 'c', 'd']


def test_parse_typed_field_list_more_complex():
    sql = '''   IN a int = 5,
                IN b text default 'abc'::text,
                IN c double precision = 9.99",
                OUT d double precision[]            '''
    tokens = sqlparse.parse(sql)[0].flatten()
    args = list(parse_typed_field_list(tokens))
    assert [arg.name for arg in args] == ['a', 'b', 'c', 'd']
    assert [arg.mode for arg in args] == ['IN', 'IN', 'IN', 'OUT']


def test_parse_typed_field_list_no_arg_names():
    sql = 'int, double precision, text'
    tokens = sqlparse.parse(sql)[0].flatten()
    args = list(parse_typed_field_list(tokens))
    assert(len(args) == 3)


def test_table_column_names():
    tbl_str = '''
        x INT,
        y DOUBLE PRECISION,
        z TEXT '''
    names = list(field_names(tbl_str, mode_filter=None))
    assert names == ['x', 'y', 'z']


def test_argument_names():
    func_header = 'IN x INT DEFAULT 2, OUT y DOUBLE PRECISION'
    names = field_names(func_header, mode_filter=['OUT', 'INOUT'])
    assert list(names) == ['y']


def test_empty_arg_list():
    # happens for e.g. parameter-less functions like now()
    names = field_names('')
    assert list(names) == []
