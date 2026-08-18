import pytest
from click.testing import CliRunner

from pgcli.main import cli, PGCli


def write_config(tmp_path, body):
    cfg = tmp_path / "config"
    cfg.write_text(body)
    return cfg


@pytest.fixture
def isolate_config(monkeypatch, tmp_path):
    # Keep the real config dir out of the picture. get_config() writes its
    # default template under here when a config file does not exist yet.
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    return tmp_path


def test_list_dsn_fresh_config(isolate_config):
    # No config file exists yet. --list-dsn used to read the not-yet-written
    # config before PGCli() created it, hit a KeyError on the missing
    # [alias_dsn] section, and print "Invalid DSNs found" with exit code 1.
    # It should just report no aliases and exit cleanly.
    cfg = isolate_config / "config"
    runner = CliRunner()
    result = runner.invoke(cli, ["--pgclirc", str(cfg), "--list-dsn"])
    assert result.exit_code == 0
    assert "Invalid DSNs" not in result.output
    assert result.output.strip() == ""


def test_list_dsn_lists_aliases(isolate_config):
    cfg = write_config(
        isolate_config,
        "[alias_dsn]\n"
        "foo = postgres://u:p@localhost:5432/foo\n"
        "bar = postgres://u:p@localhost:5432/bar\n",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--pgclirc", str(cfg), "--list-dsn"])
    assert result.exit_code == 0
    assert "foo : postgres://u:p@localhost:5432/foo" in result.output
    assert "bar : postgres://u:p@localhost:5432/bar" in result.output


def test_dsn_alias_resolves(isolate_config, monkeypatch):
    cfg = write_config(
        isolate_config,
        "[alias_dsn]\nfoo = postgres://u:p@localhost:5432/foo\n",
    )
    captured = {}

    def fake_connect(self, *args, **kwargs):
        # connect_uri() parses the alias URI and calls connect() with the
        # resolved parts, so recording them proves the alias was found.
        captured.update(kwargs)

        class DummyExec:
            def run(self, cmd):
                return []

            def get_timezone(self):
                return "UTC"

            def set_timezone(self, *a, **k):
                pass

        self.pgexecute = DummyExec()

    monkeypatch.setattr(PGCli, "connect", fake_connect)

    runner = CliRunner()
    result = runner.invoke(cli, ["--pgclirc", str(cfg), "-D", "foo", "--ping"])
    assert result.exit_code == 0
    assert "Could not find a DSN" not in result.output
    assert captured.get("database") == "foo"
    assert captured.get("host") == "localhost"


def test_dsn_alias_missing(isolate_config):
    cfg = write_config(
        isolate_config,
        "[alias_dsn]\nfoo = postgres://u:p@localhost:5432/foo\n",
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["--pgclirc", str(cfg), "-D", "does-not-exist"])
    assert result.exit_code == 1
    assert "Could not find a DSN with alias does-not-exist" in result.output
