import json
import pytest
from pgcli import pgcompleter
import tempfile
from prompt_toolkit.document import Document


def path_completions(completer, text):
    document = Document(text=text, cursor_position=len(text))
    return list(completer.get_completions(document, None))


def test_load_alias_map_file_missing_file():
    with pytest.raises(
        pgcompleter.InvalidMapFile,
        match=r"Cannot read alias_map_file - /path/to/non-existent/file.json does not exist$",
    ):
        pgcompleter.load_alias_map_file("/path/to/non-existent/file.json")


def test_load_alias_map_file_invalid_json(tmp_path):
    fpath = tmp_path / "foo.json"
    fpath.write_text("this is not valid json")
    with pytest.raises(pgcompleter.InvalidMapFile, match=r".*is not valid json$"):
        pgcompleter.load_alias_map_file(str(fpath))


def test_path_completion_filters_files_for_cd(tmp_path, monkeypatch):
    (tmp_path / "folder").mkdir()
    (tmp_path / "file.sql").touch()
    monkeypatch.chdir(tmp_path)
    completer = pgcompleter.PGCompleter()

    assert [completion.text for completion in path_completions(completer, r"\ls f")] == ["ile.sql", "older"]
    assert [completion.text for completion in path_completions(completer, r"\cd f")] == ["older"]


def test_path_completion_handles_spaces(tmp_path, monkeypatch):
    directory = tmp_path / "space directory"
    directory.mkdir()
    (directory / "query.sql").touch()
    monkeypatch.chdir(tmp_path)

    completions = path_completions(pgcompleter.PGCompleter(), r"\i space directory/q")

    assert [completion.text for completion in completions] == ["uery.sql"]


@pytest.mark.parametrize(
    "table_name, alias",
    [
        ("SomE_Table", "SET"),
        ("SOmeTabLe", "SOTL"),
        ("someTable", "T"),
    ],
)
def test_generate_alias_uses_upper_case_letters_from_name(table_name, alias):
    assert pgcompleter.generate_alias(table_name) == alias


@pytest.mark.parametrize(
    "table_name, alias",
    [
        ("some_tab_le", "stl"),
        ("s_ome_table", "sot"),
        ("sometable", "s"),
    ],
)
def test_generate_alias_uses_first_char_and_every_preceded_by_underscore(table_name, alias):
    assert pgcompleter.generate_alias(table_name) == alias


@pytest.mark.parametrize(
    "table_name, alias_map, alias",
    [
        ("some_table", {"some_table": "my_alias"}, "my_alias"),
        pytest.param("some_other_table", {"some_table": "my_alias"}, "sot", id="no_match_in_map"),
    ],
)
def test_generate_alias_can_use_alias_map(table_name, alias_map, alias):
    assert pgcompleter.generate_alias(table_name, alias_map) == alias


@pytest.mark.parametrize(
    "table_name, alias_map, alias",
    [
        ("some_table", {"some_table": "my_alias"}, "my_alias"),
    ],
)
def test_pgcompleter_alias_uses_configured_alias_map(table_name, alias_map, alias):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as alias_map_file:
        alias_map_file.write(json.dumps(alias_map))
        alias_map_file.seek(0)
        completer = pgcompleter.PGCompleter(
            settings={
                "generate_aliases": True,
                "alias_map_file": alias_map_file.name,
            }
        )
        assert completer.alias(table_name, []) == alias


@pytest.mark.parametrize(
    "table_name, alias_map, alias",
    [
        ("SomeTable", {"SomeTable": "my_alias"}, "my_alias"),
    ],
)
def test_generate_alias_prefers_alias_over_upper_case_name(table_name, alias_map, alias):
    assert pgcompleter.generate_alias(table_name, alias_map) == alias


@pytest.mark.parametrize(
    "table_name, alias",
    [
        ("Some_tablE", "SE"),
        ("SomeTab_le", "ST"),
    ],
)
def test_generate_alias_prefers_upper_case_name_over_underscore_name(table_name, alias):
    assert pgcompleter.generate_alias(table_name) == alias


@pytest.mark.parametrize(
    "name, expected",
    [
        (b"pg_catalog", "pg_catalog"),
        (b"public", "public"),
        (b"Mixed Case", '"Mixed Case"'),
        (b"select", '"select"'),
    ],
)
def test_escape_name_accepts_bytes(name, expected):
    """Identifiers arrive as bytes under encodings psycopg cannot decode."""
    completer = pgcompleter.PGCompleter()
    assert completer.escape_name(name) == expected
    assert completer.escaped_names([name]) == [expected]
