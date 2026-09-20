import io
import os
import re
import stat

import pytest

from pgcli.config import ensure_dir_exists, load_config, skip_initial_comment


def test_ensure_file_parent(tmpdir):
    subdir = tmpdir.join("subdir")
    rcfile = subdir.join("rcfile")
    ensure_dir_exists(str(rcfile))


def test_ensure_existing_dir(tmpdir):
    rcfile = str(tmpdir.mkdir("subdir").join("rcfile"))

    # should just not raise
    ensure_dir_exists(rcfile)


def test_ensure_other_create_error(tmpdir):
    subdir = tmpdir.join('subdir"')
    rcfile = subdir.join("rcfile")

    # trigger an  oserror that isn't "directory already exists"
    os.chmod(str(tmpdir), stat.S_IREAD)

    with pytest.raises(OSError):
        ensure_dir_exists(str(rcfile))


@pytest.mark.parametrize(
    "text, skipped_lines",
    (
        ("abc\n", 1),
        ("#[section]\ndef\n[section]", 2),
        ("[section]", 0),
    ),
)
def test_skip_initial_comment(text, skipped_lines):
    assert skip_initial_comment(io.StringIO(text)) == skipped_lines


def test_load_config_preserves_pgclirc_compatibility(tmp_path):
    defaults = tmp_path / "defaults"
    defaults.write_text(
        "[main]\nEnabled = True\ncount = 2\nitems = one, 'two, too'\nprompt = 'default'\n[CaseSensitive]\nMixedCase = default\n",
        encoding="utf-8",
    )
    user = tmp_path / "config"
    user.write_text(
        "[main]\nprompt = '100% # ready'\nunquoted = value# comment\n[CaseSensitive]\nMixedCase = override\nmixedcase = separate\n",
        encoding="utf-8",
    )

    config = load_config(str(user), str(defaults))

    assert config["main"].as_bool("Enabled") is True
    assert config["main"].as_int("count") == 2
    assert config["main"].as_list("items") == ["one", "two, too"]
    assert config["main"]["prompt"] == "100% # ready"
    assert config["main"]["unquoted"] == "value"
    assert config["CaseSensitive"] == {"MixedCase": "override", "mixedcase": "separate"}


def test_config_write_keeps_comments_and_round_trips_queries(tmp_path):
    from pgspecial.namedqueries import NamedQueries

    filename = tmp_path / "config"
    filename.write_text(
        "# user's heading\n[named queries]\n# keep this explanation\nold = select 1 # keep inline too\n"
        "remove = select 2\n\n[main]\nprompt = '# > 100%'\n",
        encoding="utf-8",
    )
    config = load_config(str(filename))

    queries = NamedQueries.from_config(config)
    queries.save("old", "select 3\nfrom numbers")
    queries.save("NewQuery", "select '#', '100%'")
    assert queries.delete("remove") == "remove: Deleted"

    contents = filename.read_text(encoding="utf-8")
    assert "# user's heading" in contents
    assert "# keep this explanation" in contents
    assert "# keep inline too" in contents
    assert "remove =" not in contents
    reloaded = load_config(str(filename))
    assert reloaded["named queries"] == {
        "old": "select 3\nfrom numbers",
        "NewQuery": "select '#', '100%'",
    }
    assert reloaded["main"]["prompt"] == "# > 100%"


def test_configobj_quoted_lists_are_preserved(tmp_path):
    filename = tmp_path / "config"
    filename.write_text(
        '[main]\nitems = "delete", "update"\nquoted_item = "delete, update"\n',
        encoding="utf-8",
    )

    config = load_config(str(filename))

    assert config["main"].as_list("items") == ["delete", "update"]
    assert config["main"].as_list("quoted_item") == ["delete, update"]


def test_configobj_lists_preserve_backslashes(tmp_path):
    filename = tmp_path / "config"
    filename.write_text("[main]\npaths = C:\\tmp\\file, D:\\data\n", encoding="utf-8")

    config = load_config(str(filename))

    assert config["main"].as_list("paths") == [r"C:\tmp\file", r"D:\data"]


@pytest.mark.parametrize(
    "source, expected",
    [
        ("", [""]),
        ('""', [""]),
        ("delete,", ["delete"]),
        (",", []),
        ('","', [","]),
        ("','", [","]),
    ],
)
def test_configobj_list_edge_cases(tmp_path, source, expected):
    filename = tmp_path / "config"
    filename.write_text(f"[main]\nitems = {source}\n", encoding="utf-8")

    assert load_config(str(filename))["main"].as_list("items") == expected


def test_escaped_quote_does_not_expose_hash_comment(tmp_path):
    filename = tmp_path / "config"
    filename.write_text("[main]\nprompt = 'Bob\\'s # tag'\n", encoding="utf-8")

    config = load_config(str(filename))

    assert config["main"]["prompt"] == r"Bob\'s # tag"


def test_default_is_an_ordinary_case_sensitive_section(tmp_path):
    filename = tmp_path / "config"
    filename.write_text("[DEFAULT]\nOnlyHere = value\n[main]\nprompt = ready\n", encoding="utf-8")

    config = load_config(str(filename))

    assert config["DEFAULT"] == {"OnlyHere": "value"}
    assert config["main"] == {"prompt": "ready"}


@pytest.mark.parametrize(
    "query",
    ["select payload #> path", " select trailing ", '''select 'one', "two" #> path'''],
)
def test_named_query_write_quotes_hashes_and_surrounding_whitespace(tmp_path, query):
    from pgspecial.namedqueries import NamedQueries

    filename = tmp_path / "config"
    filename.write_text("[named queries]\n", encoding="utf-8")
    config = load_config(str(filename))

    NamedQueries.from_config(config).save("q", query)

    assert load_config(str(filename))["named queries"]["q"] == query


def test_configobj_multiline_queries_update_and_delete(tmp_path):
    from pgspecial.namedqueries import NamedQueries

    filename = tmp_path / "config"
    filename.write_text(
        "[named queries]\nold = '''select 1\nfrom numbers''' # keep old comment\n"
        "remove = \"\"\"select 2\nfrom numbers\nwhere false\"\"\" # keep remove comment\n"
        "[main]\nprompt = original\n",
        encoding="utf-8",
    )
    config = load_config(str(filename))

    queries = NamedQueries.from_config(config)
    queries.save("old", "select 3\nfrom updated")
    assert queries.delete("remove") == "remove: Deleted"
    config["main"]["prompt"] = "'quoted prompt'"
    config.write()

    contents = filename.read_text(encoding="utf-8")
    assert "from numbers'''" not in contents
    assert 'where false"""' not in contents
    assert 'old = """select 3\nfrom updated""" # keep old comment' in contents
    assert "# keep remove comment" in contents
    reloaded = load_config(str(filename))
    assert reloaded["named queries"] == {"old": "select 3\nfrom updated"}
    assert reloaded["main"]["prompt"] == "'quoted prompt'"


@pytest.mark.parametrize("quote", ['"""', "'''"])
def test_multiline_queries_are_lossless_across_writes_and_delete(tmp_path, quote):
    filename = tmp_path / "config"
    original = "\nselect 1\n\n# literal hash\n; literal semicolon\n  indented\n"
    filename.write_text(
        f"[named queries]\nq = {quote}{original}{quote}\nkeep = select 2 # keep\n",
        encoding="utf-8",
    )

    config = load_config(str(filename))
    assert config["named queries"]["q"] == original
    config["named queries"]["new"] = original
    config.write()
    assert load_config(str(filename))["named queries"]["new"] == original

    reloaded = load_config(str(filename))
    reloaded.write()
    del reloaded["named queries"]["q"]
    reloaded.write()
    result = load_config(str(filename))["named queries"]
    assert "q" not in result
    assert result["new"] == original
    assert result["keep"] == "select 2"
    assert "# keep" in filename.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "contents, message",
    [
        ("option = value\n[main]\nprompt = ready\n", "root-level options"),
        ("[main]\n[[nested]]\noption = value\n", "nested [[sections]]"),
    ],
)
def test_unsupported_configobj_structures_fail_clearly(tmp_path, contents, message):
    filename = tmp_path / "config"
    filename.write_text(contents, encoding="utf-8")

    with pytest.raises(ValueError, match=re.escape(message)):
        load_config(str(filename))
