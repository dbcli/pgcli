from unittest.mock import patch

from click.testing import CliRunner

from pgcli.main import cli, format_output, OutputSettings, PGCli


def test_no_timings_flag_passed_to_pgcli():
    runner = CliRunner()
    with patch.object(PGCli, "__init__", autospec=True, return_value=None) as mock_pgcli:
        runner.invoke(cli, ["--no-timings", "mydb"])
        assert mock_pgcli.call_args[1]["no_timings"] is True


def test_no_status_flag_passed_to_pgcli():
    runner = CliRunner()
    with patch.object(PGCli, "__init__", autospec=True, return_value=None) as mock_pgcli:
        runner.invoke(cli, ["--no-status", "mydb"])
        assert mock_pgcli.call_args[1]["no_status"] is True


def test_both_default_to_false():
    runner = CliRunner()
    with patch.object(PGCli, "__init__", autospec=True, return_value=None) as mock_pgcli:
        runner.invoke(cli, ["mydb"])
        assert mock_pgcli.call_args[1]["no_timings"] is False
        assert mock_pgcli.call_args[1]["no_status"] is False


def test_no_timings_turns_off_timing_only():
    """The point of having two flags: each one leaves the other alone."""
    cli_obj = PGCli(no_timings=True)

    assert cli_obj.pgspecial.timing_enabled is False
    assert cli_obj.show_status is True


def test_no_status_turns_off_status_only():
    cli_obj = PGCli(no_status=True)

    assert cli_obj.show_status is False
    assert cli_obj.pgspecial.timing_enabled is True


def test_tuples_only_still_turns_off_both():
    """-t stays the psql-compatible shorthand for both."""
    cli_obj = PGCli(tuples_only=True)

    assert cli_obj.show_status is False
    assert cli_obj.pgspecial.timing_enabled is False


def test_no_status_suppresses_only_the_footer():
    settings = OutputSettings(table_format="psql", show_status=False)
    output = "\n".join(format_output("Title", [(1,)], ["a"], "SELECT 1", settings))

    assert "SELECT 1" not in output
    # Rows, headers and title are untouched.
    assert "Title" in output
    assert "a" in output and "1" in output


def test_status_footer_is_printed_by_default():
    settings = OutputSettings(table_format="psql")
    output = "\n".join(format_output("Title", [(1,)], ["a"], "SELECT 1", settings))

    assert "SELECT 1" in output
