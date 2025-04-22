import pytest
from click.testing import CliRunner

from pgcli.main import cli, PGCli


@pytest.fixture
def dummy_exec(monkeypatch, tmp_path):
    # Capture executed commands
    # Isolate config directory for tests
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    dummy_cmds = []

    class DummyExec:
        def run(self, cmd):
            # Ignore ping SELECT 1 commands used for exiting CLI
            if cmd.strip().upper() == "SELECT 1":
                return []
            # Record init commands
            dummy_cmds.append(cmd)
            return []

        def get_timezone(self):
            return "UTC"

        def set_timezone(self, *args, **kwargs):
            pass

    def fake_connect(self, *args, **kwargs):
        self.pgexecute = DummyExec()

    monkeypatch.setattr(PGCli, "connect", fake_connect)
    return dummy_cmds


def test_init_command_option(dummy_exec):
    "Test that --init-command triggers execution of the command."
    runner = CliRunner()
    # Use a custom init command and --ping to exit the CLI after init commands
    result = runner.invoke(
        cli, ["--init-command", "SELECT foo", "--ping", "db", "user"]
    )
    assert result.exit_code == 0
    # Should print the init command
    assert "Running init commands: SELECT foo" in result.output
    # Should exit via ping
    assert "PONG" in result.output
    # DummyExec should have recorded only the init command
    assert dummy_exec == ["SELECT foo"]


def test_init_commands_from_config(dummy_exec, tmp_path):
    """
    Test that init commands defined in the config file are executed on startup.
    """
    # Create a temporary config file with init-commands
    config_file = tmp_path / "pgclirc_test"
    config_file.write_text(
        "[main]\n[init-commands]\nfirst = SELECT foo;\nsecond = SELECT bar;\n"
    )

    runner = CliRunner()
    # Use --ping to exit the CLI after init commands
    result = runner.invoke(
        cli, ["--pgclirc", str(config_file.absolute()), "--ping", "testdb", "user"]
    )
    assert result.exit_code == 0
    # Should print both init commands in order (note trailing semicolons cause double ';;')
    assert "Running init commands: SELECT foo;; SELECT bar;" in result.output
    # DummyExec should have recorded both commands
    assert dummy_exec == ["SELECT foo;", "SELECT bar;"]


def test_init_commands_option_and_config(dummy_exec, tmp_path):
    """
    Test that CLI-provided init command is appended after config-defined commands.
    """
    # Create a temporary config file with init-commands
    config_file = tmp_path / "pgclirc_test"
    config_file.write_text("[main]\n [init-commands]\nfirst = SELECT foo;\n")

    runner = CliRunner()
    # Use --ping to exit the CLI after init commands
    result = runner.invoke(
        cli,
        [
            "--pgclirc",
            str(config_file),
            "--init-command",
            "SELECT baz;",
            "--ping",
            "testdb",
            "user",
        ],
    )
    assert result.exit_code == 0
    # Should print config command followed by CLI option (double ';' between commands)
    assert "Running init commands: SELECT foo;; SELECT baz;" in result.output
    # DummyExec should record both commands in order
    assert dummy_exec == ["SELECT foo;", "SELECT baz;"]
