from pgcli.packages.sqlcompletion import suggest_type
from test_sqlcompletion import sorted_dicts

def test_slash_suggests_special():
    suggestions = suggest_type('\\', '\\')
    assert sorted_dicts(suggestions) == sorted_dicts(
        [{'type': 'special'}])

def test_slash_d_suggests_special():
    suggestions = suggest_type('\\d', '\\d')
    assert sorted_dicts(suggestions) == sorted_dicts(
        [{'type': 'special'}])

def test_dn_suggests_schemata():
    suggestions = suggest_type('\\dn ', '\\dn ')
    assert suggestions == [{'type': 'schema'}]

    suggestions = suggest_type('\\dn xxx', '\\dn xxx')
    assert suggestions == [{'type': 'schema'}]

def test_d_suggests_tables_views_and_schemas():
    suggestions = suggest_type('\d ', '\d ')
    assert sorted_dicts(suggestions) == sorted_dicts([
            {'type': 'schema'},
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []}])

    suggestions = suggest_type('\d xxx', '\d xxx')
    assert sorted_dicts(suggestions) == sorted_dicts([
            {'type': 'schema'},
            {'type': 'table', 'schema': []},
            {'type': 'view', 'schema': []}])

def test_d_dot_suggests_schema_qualified_tables_or_views():
    suggestions = suggest_type('\d myschema.', '\d myschema.')
    assert suggestions == [{'type': 'table', 'schema': 'myschema'},
                           {'type': 'view', 'schema': 'myschema'}]

    suggestions = suggest_type('\d myschema.xxx', '\d myschema.xxx')
    assert suggestions == [{'type': 'table', 'schema': 'myschema'},
                           {'type': 'view', 'schema': 'myschema'}]

def test_df_suggests_schema_or_function():
    suggestions = suggest_type('\\df xxx', '\\df xxx')
    assert sorted_dicts(suggestions) == sorted_dicts([
        {'type': 'function', 'schema': []}, {'type': 'schema'}])

    suggestions = suggest_type('\\df myschema.xxx', '\\df myschema.xxx')
    assert suggestions == [{'type': 'function', 'schema': 'myschema'}]

def test_leading_whitespace_ok():
    cmd = '\\dn '
    whitespace = '   '
    suggestions = suggest_type(whitespace + cmd, whitespace + cmd)
    assert suggestions == suggest_type(cmd, cmd)


def test_dT_suggests_schema_or_datatypes():
    text = '\\dT '
    suggestions = suggest_type(text, text)
    assert sorted_dicts(suggestions) == sorted_dicts(
        [{'type': 'schema'},
         {'type': 'datatype', 'schema': []},
        ])

def test_schema_qualified_dT_suggests_datatypes():
    text = '\\dT foo.'
    suggestions = suggest_type(text, text)
    assert sorted_dicts(suggestions) == sorted_dicts(
        [{'type': 'datatype', 'schema': 'foo'}])