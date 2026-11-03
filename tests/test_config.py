import io
import os
import stat

import pytest

from pgcli.config import (
    ensure_dir_exists,
    ensure_private_file,
    skip_initial_comment,
    write_default_config,
)


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


posix_only = pytest.mark.skipif(os.name != "posix", reason="POSIX file modes")


@posix_only
def test_ensure_private_file_creates_owner_only(tmp_path):
    path = tmp_path / "history"
    ensure_private_file(str(path))
    assert path.exists() and path.read_bytes() == b""
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@posix_only
def test_ensure_private_file_tightens_existing_and_keeps_content(tmp_path):
    path = tmp_path / "history"
    path.write_text("select 1\n")
    path.chmod(0o664)
    ensure_private_file(str(path))
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert path.read_text() == "select 1\n"


@posix_only
def test_ensure_private_file_leaves_device_nodes_alone():
    # history_file = /dev/null is the usual way to record nothing; running as
    # root, a chmod here would change it for every user on the machine.
    before = os.stat("/dev/null").st_mode
    ensure_private_file("/dev/null")
    assert os.stat("/dev/null").st_mode == before


@posix_only
def test_ensure_private_file_does_not_block_on_a_fifo(tmp_path):
    import threading

    fifo = tmp_path / "history"
    os.mkfifo(fifo)
    worker = threading.Thread(target=ensure_private_file, args=(str(fifo),), daemon=True)
    worker.start()
    worker.join(timeout=5)
    assert not worker.is_alive(), "open() on a reader-less FIFO must not hang pgcli"


@posix_only
def test_ensure_private_file_ignores_a_directory(tmp_path):
    ensure_private_file(str(tmp_path))
    assert tmp_path.is_dir()


@posix_only
def test_write_default_config_is_owner_only(tmp_path):
    source = tmp_path / "pgclirc"
    source.write_text("[main]\n")
    destination = tmp_path / "config"
    write_default_config(str(source), str(destination))
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
