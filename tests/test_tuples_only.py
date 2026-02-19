from unittest.mock import patch

from click.testing import CliRunner

from pgcli.main import cli, PGCli


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


def test_tuples_only_sets_csv_noheader_format():
    """Test that tuples_only=True sets table_format to csv-noheader."""
    pgcli = PGCli(tuples_only=True)
    assert pgcli.table_format == "csv-noheader"


def test_default_table_format_without_tuples_only():
    """Test that table_format uses config default when tuples_only is False."""
    pgcli = PGCli()
    assert pgcli.table_format != "csv-noheader"  # Uses config default
