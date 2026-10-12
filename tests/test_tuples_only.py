from unittest.mock import patch

from click.testing import CliRunner

from pgcli.main import cli, format_output, OutputSettings, PGCli


def test_tuples_only_flag_passed_to_pgcli():
    """Test that -t passes tuples_only=True to PGCli."""
    runner = CliRunner()
    with patch.object(PGCli, "__init__", autospec=True, return_value=None) as mock_pgcli:
        runner.invoke(cli, ["-t", "mydb"])
        call_kwargs = mock_pgcli.call_args[1]
        assert call_kwargs["tuples_only"] is True


def test_tuples_only_long_form():
    """Test that --tuples-only passes tuples_only=True to PGCli."""
    runner = CliRunner()
    with patch.object(PGCli, "__init__", autospec=True, return_value=None) as mock_pgcli:
        runner.invoke(cli, ["--tuples-only", "mydb"])
        call_kwargs = mock_pgcli.call_args[1]
        assert call_kwargs["tuples_only"] is True


def test_tuples_only_not_set_by_default():
    """Test that tuples_only is False when -t is not used."""
    runner = CliRunner()
    with patch.object(PGCli, "__init__", autospec=True, return_value=None) as mock_pgcli:
        runner.invoke(cli, ["mydb"])
        call_kwargs = mock_pgcli.call_args[1]
        assert call_kwargs["tuples_only"] is False


def test_tuples_only_leaves_the_configured_table_format_alone():
    """-t must not hijack the table format: \\T still reports what is configured."""
    assert PGCli(tuples_only=True).table_format == PGCli().table_format


def test_tuples_only_turns_off_timing():
    """psql's -t prints no timing line."""
    assert PGCli(tuples_only=True).pgspecial.timing_enabled is False


def test_tuples_only_prints_rows_only():
    """No title, no column headers, no status footer, no table borders."""
    settings = OutputSettings(table_format="psql", tuples_only=True)
    output = list(format_output("Title", [(1, "one"), (2, "two")], ["a", "b"], "SELECT 2", settings))

    assert output == ["1  one", "2  two"]


def test_without_tuples_only_everything_is_printed():
    """The counterpart of the test above: by default nothing is suppressed."""
    settings = OutputSettings(table_format="psql", tuples_only=False)
    output = "\n".join(format_output("Title", [(1, "one")], ["a", "b"], "SELECT 1", settings))

    assert "Title" in output
    assert "a" in output and "b" in output
    assert "SELECT 1" in output


def test_tuples_only_wins_over_expanded_output():
    """With the headers gone the vertical formatter has no label column left,
    so -t falls back to the unadorned format rather than failing."""
    settings = OutputSettings(table_format="psql", expanded=True, tuples_only=True)
    output = list(format_output("Title", [(1, "one")], ["a", "b"], "SELECT 1", settings))

    assert output == ["1  one"]
