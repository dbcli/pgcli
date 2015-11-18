import pytest
from pgcli.packages.sqlcompletion import (
    suggest_type, Special, Database, Schema, Table, View, Function, Datatype)


def test_slash_suggests_special():
    suggestions = suggest_type('\\', '\\')
    assert set(suggestions) == set(
        [Special()])


def test_slash_d_suggests_special():
    suggestions = suggest_type('\\d', '\\d')
    assert set(suggestions) == set(
        [Special()])


def test_dn_suggests_schemata():
    suggestions = suggest_type('\\dn ', '\\dn ')
    assert suggestions == (Schema(),)

    suggestions = suggest_type('\\dn xxx', '\\dn xxx')
    assert suggestions == (Schema(),)


def test_d_suggests_tables_views_and_schemas():
    suggestions = suggest_type('\d ', '\d ')
    assert set(suggestions) == set([
        Schema(),
        Table(schema=None),
        View(schema=None),
    ])

    suggestions = suggest_type('\d xxx', '\d xxx')
    assert set(suggestions) == set([
        Schema(),
        Table(schema=None),
        View(schema=None),
    ])


def test_d_dot_suggests_schema_qualified_tables_or_views():
    suggestions = suggest_type('\d myschema.', '\d myschema.')
    assert set(suggestions) == set([
        Table(schema='myschema'),
        View(schema='myschema'),
    ])

    suggestions = suggest_type('\d myschema.xxx', '\d myschema.xxx')
    assert set(suggestions) == set([
        Table(schema='myschema'),
        View(schema='myschema'),
    ])


def test_df_suggests_schema_or_function():
    suggestions = suggest_type('\\df xxx', '\\df xxx')
    assert set(suggestions) == set([
        Function(schema=None),
        Schema(),
    ])

    suggestions = suggest_type('\\df myschema.xxx', '\\df myschema.xxx')
    assert suggestions == (Function(schema='myschema'),)


def test_leading_whitespace_ok():
    cmd = '\\dn '
    whitespace = '   '
    suggestions = suggest_type(whitespace + cmd, whitespace + cmd)
    assert suggestions == suggest_type(cmd, cmd)


def test_dT_suggests_schema_or_datatypes():
    text = '\\dT '
    suggestions = suggest_type(text, text)
    assert set(suggestions) == set([
        Schema(),
        Datatype(schema=None),
    ])


def test_schema_qualified_dT_suggests_datatypes():
    text = '\\dT foo.'
    suggestions = suggest_type(text, text)
    assert suggestions == (Datatype(schema='foo'),)


@pytest.mark.parametrize('command', ['\\c ', '\\connect '])
def test_c_suggests_databases(command):
    suggestions = suggest_type(command, command)
    assert suggestions == (Database(),)
