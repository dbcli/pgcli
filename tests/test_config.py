import io
import os
import stat

import pytest

from pgcli.config import ensure_dir_exists, migrate_file, skip_initial_comment, state_location


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


def test_state_location_default(monkeypatch):
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    loc = state_location()
    assert loc == os.path.expanduser("~/.local/state/pgcli/")


def test_state_location_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    loc = state_location()
    assert loc == str(tmp_path) + "/pgcli/"


def test_migrate_file_old_only(tmp_path):
    old = tmp_path / "old" / "history"
    old.parent.mkdir()
    old.write_text("cmd1\ncmd2\n")
    new = tmp_path / "new" / "history"

    migrate_file(str(old), str(new))

    assert not old.exists()
    assert new.read_text() == "cmd1\ncmd2\n"


def test_migrate_file_both_exist(tmp_path):
    old = tmp_path / "old" / "history"
    old.parent.mkdir()
    old.write_text("old content\n")
    new = tmp_path / "new" / "history"
    new.parent.mkdir()
    new.write_text("new content\n")

    migrate_file(str(old), str(new))

    # neither file should be touched
    assert old.read_text() == "old content\n"
    assert new.read_text() == "new content\n"


def test_migrate_file_old_missing(tmp_path):
    old = tmp_path / "old" / "history"
    new = tmp_path / "new" / "history"

    migrate_file(str(old), str(new))

    assert not new.exists()


def test_migrate_file_error_is_logged(tmp_path, caplog):
    import logging

    old = tmp_path / "old" / "history"
    old.parent.mkdir()
    old.write_text("cmd1\n")
    # make the destination parent directory read-only so the move fails
    new_dir = tmp_path / "new"
    new_dir.mkdir()
    os.chmod(str(new_dir), stat.S_IREAD | stat.S_IEXEC)

    new = new_dir / "subdir" / "history"

    with caplog.at_level(logging.ERROR, logger="pgcli.config"):
        migrate_file(str(old), str(new))

    assert any("Failed to migrate" in r.message for r in caplog.records)
    assert old.exists()  # original untouched since move failed


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
