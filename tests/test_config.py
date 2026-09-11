import io
import os
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
