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


def test_d_suggests_tables_and_schemas():
    suggestions = suggest_type('\d ', '\d ')
    assert sorted_dicts(suggestions) == sorted_dicts([
            {'type': 'schema'}, {'type': 'table', 'schema': []}])

    suggestions = suggest_type('\d xxx', '\d xxx')
    assert sorted_dicts(suggestions) == sorted_dicts([
            {'type': 'schema'}, {'type': 'table', 'schema': []}])

def test_d_dot_suggests_schema_qualified_tables():
    suggestions = suggest_type('\d myschema.', '\d myschema.')
    assert suggestions == [{'type': 'table', 'schema': 'myschema'}]

    suggestions = suggest_type('\d myschema.xxx', '\d myschema.xxx')
    assert suggestions == [{'type': 'table', 'schema': 'myschema'}]

def test_df_suggests_schema_or_function():
    suggestions = suggest_type('\\df xxx', '\\df xxx')
    assert sorted_dicts(suggestions) == sorted_dicts([
        {'type': 'function', 'schema': []}, {'type': 'schema'}])

    suggestions = suggest_type('\\df myschema.xxx', '\\df myschema.xxx')
    assert suggestions == [{'type': 'function', 'schema': 'myschema'}]
