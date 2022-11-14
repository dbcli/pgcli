import pytest
from pgcli import pgcompleter


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
