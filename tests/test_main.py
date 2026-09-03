import os
import platform
import re
import tempfile
import datetime
from unittest import mock

import pytest
from click.testing import CliRunner

try:
    import setproctitle
except ImportError:
    setproctitle = None

from pgcli.main import (
    cli,
    obfuscate_process_password,
    duration_in_words,
    format_output,
    get_connect_timeout,
    get_editor,
    notify_callback,
    PGCli,
    OutputSettings,
    COLOR_CODE_REGEX,
)
from pgcli.pgexecute import PGExecute
from psycopg.conninfo import conninfo_to_dict
from pgspecial.main import PAGER_OFF, PAGER_LONG_OUTPUT, PAGER_ALWAYS
from utils import dbtest, run
from collections import namedtuple


@pytest.mark.skipif(platform.system() == "Windows", reason="Not applicable in windows")
@pytest.mark.skipif(not setproctitle, reason="setproctitle not available")
def test_obfuscate_process_password():
    original_title = setproctitle.getproctitle()

    setproctitle.setproctitle("pgcli user=root password=secret host=localhost")
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    expected = "pgcli user=root password=xxxx host=localhost"
    assert title == expected

    setproctitle.setproctitle("pgcli user=root password=top secret host=localhost")
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    expected = "pgcli user=root password=xxxx host=localhost"
    assert title == expected

    setproctitle.setproctitle("pgcli user=root password=top secret")
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    expected = "pgcli user=root password=xxxx"
    assert title == expected

    setproctitle.setproctitle("pgcli postgres://root:secret@localhost/db")
    obfuscate_process_password()
    title = setproctitle.getproctitle()
    expected = "pgcli postgres://root:xxxx@localhost/db"
    assert title == expected

    setproctitle.setproctitle(original_title)


def test_format_output():
    settings = OutputSettings(table_format="psql", dcmlfmt="d", floatfmt="g")
    results = format_output("Title", [("abc", "def")], ["head1", "head2"], "test status", settings)
    expected = [
        "Title",
        "+-------+-------+",
        "| head1 | head2 |",
        "|-------+-------|",
        "| abc   | def   |",
        "+-------+-------+",
        "test status",
    ]
    assert list(results) == expected


def test_column_date_formats():
    settings = OutputSettings(
        table_format="psql",
        column_date_formats={
            "date_col": "%Y-%m-%d",
            "datetime_col": "%I:%M:%S %m/%d/%y",
        },
    )
    data = [
        ("name1", "2024-12-13T18:32:22", "2024-12-13T19:32:22", "2024-12-13T20:32:22"),
        ("name2", "2025-02-13T02:32:22", "2025-02-13T02:32:22", "2025-02-13T02:32:22"),
    ]
    headers = ["name", "date_col", "datetime_col", "unchanged_col"]

    results = format_output("Title", data, headers, "test status", settings)
    expected = [
        "Title",
        "+-------+------------+-------------------+---------------------+",
        "| name  | date_col   | datetime_col      | unchanged_col       |",
        "|-------+------------+-------------------+---------------------|",
        "| name1 | 2024-12-13 | 07:32:22 12/13/24 | 2024-12-13T20:32:22 |",
        "| name2 | 2025-02-13 | 02:32:22 02/13/25 | 2025-02-13T02:32:22 |",
        "+-------+------------+-------------------+---------------------+",
        "test status",
    ]
    assert list(results) == expected


def test_no_column_date_formats():
    """Test that not setting any column date formats returns unaltered datetime columns"""
    settings = OutputSettings(table_format="psql")
    data = [
        ("name1", "2024-12-13T18:32:22", "2024-12-13T19:32:22", "2024-12-13T20:32:22"),
        ("name2", "2025-02-13T02:32:22", "2025-02-13T02:32:22", "2025-02-13T02:32:22"),
    ]
    headers = ["name", "date_col", "datetime_col", "unchanged_col"]

    results = format_output("Title", data, headers, "test status", settings)
    expected = [
        "Title",
        "+-------+---------------------+---------------------+---------------------+",
        "| name  | date_col            | datetime_col        | unchanged_col       |",
        "|-------+---------------------+---------------------+---------------------|",
        "| name1 | 2024-12-13T18:32:22 | 2024-12-13T19:32:22 | 2024-12-13T20:32:22 |",
        "| name2 | 2025-02-13T02:32:22 | 2025-02-13T02:32:22 | 2025-02-13T02:32:22 |",
        "+-------+---------------------+---------------------+---------------------+",
        "test status",
    ]
    assert list(results) == expected


def test_format_output_truncate_on():
    settings = OutputSettings(table_format="psql", dcmlfmt="d", floatfmt="g", max_field_width=10)
    results = format_output(
        None,
        [("first field value", "second field value")],
        ["head1", "head2"],
        None,
        settings,
    )
    expected = [
        "+------------+------------+",
        "| head1      | head2      |",
        "|------------+------------|",
        "| first f... | second ... |",
        "+------------+------------+",
    ]
    assert list(results) == expected


def test_format_output_truncate_off():
    settings = OutputSettings(table_format="psql", dcmlfmt="d", floatfmt="g", max_field_width=None)
    long_field_value = ("first field " * 100).strip()
    results = format_output(None, [(long_field_value,)], ["head1"], None, settings)
    lines = list(results)
    assert lines[3] == f"| {long_field_value} |"


@dbtest
def test_format_array_output(executor):
    statement = """
    SELECT
        array[1, 2, 3]::bigint[] as bigint_array,
        '{{1,2},{3,4}}'::numeric[] as nested_numeric_array,
        '{å,魚,текст}'::text[] as 配列
    UNION ALL
    SELECT '{}', NULL, array[NULL]
    """
    results = run(executor, statement)
    expected = [
        "+--------------+----------------------+--------------+",
        "| bigint_array | nested_numeric_array | 配列         |",
        "|--------------+----------------------+--------------|",
        "| {1,2,3}      | {{1,2},{3,4}}        | {å,魚,текст} |",
        "| {}           | <null>               | {<null>}     |",
        "+--------------+----------------------+--------------+",
        "SELECT 2",
    ]
    assert list(results) == expected


@dbtest
def test_format_array_output_expanded(executor):
    statement = """
    SELECT
        array[1, 2, 3]::bigint[] as bigint_array,
        '{{1,2},{3,4}}'::numeric[] as nested_numeric_array,
        '{å,魚,текст}'::text[] as 配列
    UNION ALL
    SELECT '{}', NULL, array[NULL]
    """
    results = run(executor, statement, expanded=True)
    expected = [
        "-[ RECORD 1 ]-------------------------",
        "bigint_array         | {1,2,3}",
        "nested_numeric_array | {{1,2},{3,4}}",
        "配列                   | {å,魚,текст}",
        "-[ RECORD 2 ]-------------------------",
        "bigint_array         | {}",
        "nested_numeric_array | <null>",
        "配列                   | {<null>}",
        "SELECT 2",
    ]
    assert "\n".join(results) == "\n".join(expected)


def test_format_output_auto_expand():
    settings = OutputSettings(table_format="psql", dcmlfmt="d", floatfmt="g", max_width=100)
    table_results = format_output("Title", [("abc", "def")], ["head1", "head2"], "test status", settings)
    table = [
        "Title",
        "+-------+-------+",
        "| head1 | head2 |",
        "|-------+-------|",
        "| abc   | def   |",
        "+-------+-------+",
        "test status",
    ]
    assert list(table_results) == table
    expanded_results = format_output(
        "Title",
        [("abc", "def")],
        ["head1", "head2"],
        "test status",
        settings._replace(max_width=1),
    )
    expanded = [
        "Title",
        "-[ RECORD 1 ]-------------------------",
        "head1 | abc",
        "head2 | def",
        "test status",
    ]
    assert "\n".join(expanded_results) == "\n".join(expanded)


termsize = namedtuple("termsize", ["rows", "columns"])
test_line = "-" * 10
test_data = [
    (10, 10, "\n".join([test_line] * 7)),
    (10, 10, "\n".join([test_line] * 6)),
    (10, 10, "\n".join([test_line] * 5)),
    (10, 10, "-" * 11),
    (10, 10, "-" * 10),
    (10, 10, "-" * 9),
]

# 4 lines are reserved at the bottom of the terminal for pgcli's prompt
use_pager_when_on = [True, True, False, True, False, False]

# Can be replaced with pytest.param once we can upgrade pytest after Python 3.4 goes EOL
test_ids = [
    "Output longer than terminal height",
    "Output equal to terminal height",
    "Output shorter than terminal height",
    "Output longer than terminal width",
    "Output equal to terminal width",
    "Output shorter than terminal width",
]


@pytest.fixture
def pset_pager_mocks():
    cli = PGCli()
    cli.watch_command = None
    with (
        mock.patch("pgcli.main.click.echo") as mock_echo,
        mock.patch("pgcli.main.click.echo_via_pager") as mock_echo_via_pager,
        mock.patch.object(cli, "prompt_app") as mock_app,
    ):
        yield cli, mock_echo, mock_echo_via_pager, mock_app


@pytest.mark.parametrize("term_height,term_width,text", test_data, ids=test_ids)
def test_pset_pager_off(term_height, term_width, text, pset_pager_mocks):
    cli, mock_echo, mock_echo_via_pager, mock_cli = pset_pager_mocks
    mock_cli.output.get_size.return_value = termsize(rows=term_height, columns=term_width)

    with mock.patch.object(cli.pgspecial, "pager_config", PAGER_OFF):
        cli.echo_via_pager(text)

    mock_echo.assert_called()
    mock_echo_via_pager.assert_not_called()


@pytest.mark.parametrize("term_height,term_width,text", test_data, ids=test_ids)
def test_pset_pager_always(term_height, term_width, text, pset_pager_mocks):
    cli, mock_echo, mock_echo_via_pager, mock_cli = pset_pager_mocks
    mock_cli.output.get_size.return_value = termsize(rows=term_height, columns=term_width)

    with mock.patch.object(cli.pgspecial, "pager_config", PAGER_ALWAYS):
        cli.echo_via_pager(text)

    mock_echo.assert_not_called()
    mock_echo_via_pager.assert_called()


pager_on_test_data = [l + (r,) for l, r in zip(test_data, use_pager_when_on)]


@pytest.mark.parametrize("term_height,term_width,text,use_pager", pager_on_test_data, ids=test_ids)
def test_pset_pager_on(term_height, term_width, text, use_pager, pset_pager_mocks):
    cli, mock_echo, mock_echo_via_pager, mock_cli = pset_pager_mocks
    mock_cli.output.get_size.return_value = termsize(rows=term_height, columns=term_width)

    with mock.patch.object(cli.pgspecial, "pager_config", PAGER_LONG_OUTPUT):
        cli.echo_via_pager(text)

    if use_pager:
        mock_echo.assert_not_called()
        mock_echo_via_pager.assert_called()
    else:
        mock_echo_via_pager.assert_not_called()
        mock_echo.assert_called()


@pytest.mark.parametrize(
    "text,expected_length",
    [
        (
            "22200K .......\u001b[0m\u001b[91m... .......... ...\u001b[0m\u001b[91m.\u001b[0m\u001b[91m...... .........\u001b[0m\u001b[91m.\u001b[0m\u001b[91m \u001b[0m\u001b[91m.\u001b[0m\u001b[91m.\u001b[0m\u001b[91m.\u001b[0m\u001b[91m.\u001b[0m\u001b[91m...... 50% 28.6K 12m55s",  # noqa: E501
            78,
        ),
        ("=\u001b[m=", 2),
        ("-\u001b]23\u0007-", 2),
    ],
)
def test_color_pattern(text, expected_length):
    assert len(COLOR_CODE_REGEX.sub("", text)) == expected_length


@dbtest
def test_i_works(tmpdir, executor):
    sqlfile = tmpdir.join("test.sql")
    sqlfile.write("SELECT NOW()")
    rcfile = str(tmpdir.join("rcfile"))
    cli = PGCli(pgexecute=executor, pgclirc_file=rcfile)
    statement = r"\i {0}".format(sqlfile)
    run(executor, statement, pgspecial=cli.pgspecial)


@dbtest
def test_toggle_verbose_errors(executor):
    cli = PGCli(pgexecute=executor)

    cli._evaluate_command("\\v on")
    assert cli.verbose_errors
    output, _ = cli._evaluate_command("SELECT 1/0")
    assert "SQLSTATE" in output[0]

    cli._evaluate_command("\\v off")
    assert not cli.verbose_errors
    output, _ = cli._evaluate_command("SELECT 1/0")
    assert "SQLSTATE" not in output[0]

    cli._evaluate_command("\\v")
    assert cli.verbose_errors


@dbtest
def test_echo_works(executor):
    cli = PGCli(pgexecute=executor)
    statement = r"\echo asdf"
    result = run(executor, statement, pgspecial=cli.pgspecial)
    assert result == ["asdf"]


@dbtest
def test_qecho_works(executor):
    cli = PGCli(pgexecute=executor)
    statement = r"\qecho asdf"
    result = run(executor, statement, pgspecial=cli.pgspecial)
    assert result == ["asdf"]


@dbtest
def test_logfile_works(executor):
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = f"{tmpdir}/tempfile.log"
        cli = PGCli(pgexecute=executor, log_file=log_file)
        statement = r"\qecho hello!"
        cli.execute_command(statement)
        with open(log_file, "r") as f:
            log_contents = f.readlines()
        assert datetime.datetime.fromisoformat(log_contents[0].strip())
        assert log_contents[1].strip() == r"\qecho hello!"
        assert log_contents[2].strip() == "hello!"


@dbtest
def test_logfile_unwriteable_file(executor):
    cli = PGCli(pgexecute=executor)
    statement = r"\log-file forbidden.log"
    with mock.patch("builtins.open") as mock_open:
        mock_open.side_effect = PermissionError("[Errno 13] Permission denied: 'forbidden.log'")
        result = run(executor, statement, pgspecial=cli.pgspecial)
    assert result == ["[Errno 13] Permission denied: 'forbidden.log'\nLogfile capture disabled"]


@dbtest
def test_watch_works(executor):
    cli = PGCli(pgexecute=executor)

    def run_with_watch(query, target_call_count=1, expected_output="", expected_timing=None):
        """
        :param query: Input to the CLI
        :param target_call_count: Number of times the user lets the command run before Ctrl-C
        :param expected_output: Substring expected to be found for each executed query
        :param expected_timing: value `time.sleep` expected to be called with on every invocation
        """
        with mock.patch.object(cli, "echo_via_pager") as mock_echo, mock.patch("pgcli.main.sleep") as mock_sleep:
            mock_sleep.side_effect = [None] * (target_call_count - 1) + [KeyboardInterrupt]
            cli.handle_watch_command(query)
        # Validate that sleep was called with the right timing
        for i in range(target_call_count - 1):
            assert mock_sleep.call_args_list[i][0][0] == expected_timing
        # Validate that the output of the query was expected
        assert mock_echo.call_count == target_call_count
        for i in range(target_call_count):
            assert expected_output in mock_echo.call_args_list[i][0][0]

    # With no history, it errors.
    with mock.patch("pgcli.main.click.secho") as mock_secho:
        cli.handle_watch_command(r"\watch 2")
    mock_secho.assert_called()
    assert r"\watch cannot be used with an empty query" in mock_secho.call_args_list[0][0][0]

    # Usage 1: Run a query and then re-run it with \watch across two prompts.
    run_with_watch("SELECT 111", expected_output="111")
    run_with_watch("\\watch 10", target_call_count=2, expected_output="111", expected_timing=10)

    # Usage 2: Run a query and \watch via the same prompt.
    run_with_watch(
        "SELECT 222; \\watch 4",
        target_call_count=3,
        expected_output="222",
        expected_timing=4,
    )

    # Usage 3: Re-run the last watched command with a new timing
    run_with_watch("\\watch 5", target_call_count=4, expected_output="222", expected_timing=5)


@dbtest
def test_execute_statements_splits_a_block(executor):
    """A multi-statement block runs one statement at a time, like psql -f."""
    cli = PGCli(pgexecute=executor)
    with mock.patch.object(cli, "echo_via_pager") as mock_echo:
        ok = cli._execute_statements("select 111;\nselect 222;")
    assert ok is True
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    assert len(outputs) == 2
    assert "111" in outputs[0] and "222" not in outputs[0]
    assert "222" in outputs[1] and "111" not in outputs[1]


@dbtest
def test_execute_statements_watch_repeats_only_its_own_statement(executor):
    r"""Regression: \watch at the end of a file repeated the WHOLE file."""
    cli = PGCli(pgexecute=executor)
    with mock.patch.object(cli, "echo_via_pager") as mock_echo, mock.patch("pgcli.main.sleep") as mock_sleep:
        mock_sleep.side_effect = [None, KeyboardInterrupt]
        cli._execute_statements("select 111;\nselect 222; \\watch 4")
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    assert "111" in outputs[0]
    for out in outputs[1:]:
        assert "222" in out
        assert "111" not in out, "\\watch repeated the whole block, not just its statement"
    assert mock_sleep.call_args_list[0][0][0] == 4


@dbtest
def test_execute_statements_bare_watch_uses_previous_statement(executor):
    r"""A \watch alone on its line picks up the statement before it."""
    cli = PGCli(pgexecute=executor)
    with mock.patch.object(cli, "echo_via_pager") as mock_echo, mock.patch("pgcli.main.sleep") as mock_sleep:
        mock_sleep.side_effect = [KeyboardInterrupt]
        cli._execute_statements("select 333;\n\\watch 5")
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    assert len(outputs) >= 2
    for out in outputs:
        assert "333" in out
    assert mock_sleep.call_args_list[0][0][0] == 5


@dbtest
def test_execute_statements_on_error_stop_halts(executor):
    """With on_error = STOP (the default) the first failure stops the block."""
    cli = PGCli(pgexecute=executor)
    assert cli.on_error == "STOP"
    with mock.patch.object(cli, "echo_via_pager") as mock_echo:
        ok = cli._execute_statements("select boom_not_a_column;\nselect 444;")
    assert ok is False
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    assert not any("444" in out for out in outputs), "the statement after the failure still ran"


@dbtest
def test_execute_statements_on_error_resume_continues(executor):
    """With on_error = RESUME the block keeps going after a failure."""
    cli = PGCli(pgexecute=executor)
    cli.on_error = "RESUME"
    with mock.patch.object(cli, "echo_via_pager") as mock_echo:
        ok = cli._execute_statements("select boom_not_a_column;\nselect 444;")
    assert ok is False
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    assert any("444" in out for out in outputs)


@dbtest
@dbtest
def test_execute_statements_metacommand_spans_only_its_line(executor):
    """psql cuts a backslash command at its newline: a metacommand followed
    by SQL must not swallow the SQL (sqlparse only cuts at semicolons)."""
    cli = PGCli(pgexecute=executor)
    with mock.patch.object(cli, "echo_via_pager") as mock_echo:
        ok = cli._execute_statements("\\echo hola\nselect 42 as x;")
    assert ok is True
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    # Two separate outputs: the echo, then a real result table. Without the
    # line cut there is a single output where \echo swallowed the select and
    # repeated its text, which is why the select text alone proves nothing.
    assert len(outputs) == 2
    assert "hola" in outputs[0]
    assert "42" in outputs[1] and "hola" not in outputs[1]
    assert "SELECT 1" in outputs[1], "the select did not actually run"


@dbtest
def test_execute_statements_consecutive_metacommands(executor):
    """Several backslash commands on consecutive lines each run on their own."""
    cli = PGCli(pgexecute=executor)
    with mock.patch.object(cli, "echo_via_pager") as mock_echo:
        ok = cli._execute_statements("\\echo uno\n\\echo dos\nselect 7 as x;")
    assert ok is True
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    assert any("uno" in out and "dos" not in out for out in outputs)
    assert any("dos" in out and "uno" not in out for out in outputs)
    assert any("7" in out for out in outputs)


@dbtest
def test_execute_statements_sql_then_metacommand(executor):
    """A metacommand after SQL still runs alone, and the SQL after it too."""
    cli = PGCli(pgexecute=executor)
    with mock.patch.object(cli, "echo_via_pager") as mock_echo:
        ok = cli._execute_statements("select 1 as a;\n\\echo medio\nselect 2 as b;")
    assert ok is True
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    assert len(outputs) == 3
    assert "medio" in outputs[1]


def test_execute_statements_does_not_split_inside_literals(executor):
    """Semicolons inside string literals are not statement boundaries."""
    cli = PGCli(pgexecute=executor)
    with mock.patch.object(cli, "echo_via_pager") as mock_echo:
        ok = cli._execute_statements("select 'a;b' as x;")
    assert ok is True
    outputs = [c[0][0] for c in mock_echo.call_args_list]
    assert len(outputs) == 1
    assert "a;b" in outputs[0]


def test_file_mode_runs_statements(tmpdir):
    """-f wiring: the file content goes through _execute_statements."""
    sql_file = tmpdir.join("script.sql")
    sql_file.write("select 1;\nselect 2;")
    cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
    cli.input_files = [str(sql_file)]
    with mock.patch.object(cli, "_execute_statements", return_value=True) as mock_exec:
        with pytest.raises(SystemExit) as e:
            cli.run_cli()
    assert e.value.code == 0
    mock_exec.assert_called_once_with("select 1;\nselect 2;")


def test_missing_rc_dir(tmpdir):
    rcfile = str(tmpdir.join("subdir").join("rcfile"))

    PGCli(pgclirc_file=rcfile)
    assert os.path.exists(rcfile)


def test_quoted_db_uri(tmpdir):
    with mock.patch.object(PGCli, "connect") as mock_connect:
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        cli.connect_uri("postgres://bar%5E:%5Dfoo@baz.com/testdb%5B")
    mock_connect.assert_called_with(database="testdb[", host="baz.com", user="bar^", passwd="]foo")


def test_pg_service_file(tmpdir):
    with mock.patch.object(PGCli, "connect") as mock_connect:
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        with open(tmpdir.join(".pg_service.conf").strpath, "w") as service_conf:
            service_conf.write(
                """File begins with a comment
            that is not a comment
            # or maybe a comment after all
            because psql is crazy

            [myservice]
            host=a_host
            user=a_user
            port=5433
            password=much_secure
            dbname=a_dbname

            [my_other_service]
            host=b_host
            user=b_user
            port=5435
            dbname=b_dbname
            """
            )
        os.environ["PGSERVICEFILE"] = tmpdir.join(".pg_service.conf").strpath
        cli.connect_service("myservice", "another_user")
        mock_connect.assert_called_with(
            database="a_dbname",
            host="a_host",
            user="another_user",
            port="5433",
            passwd="much_secure",
        )

    with mock.patch.object(PGExecute, "__init__") as mock_pgexecute:
        mock_pgexecute.return_value = None
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        os.environ["PGPASSWORD"] = "very_secure"
        cli.connect_service("my_other_service", None)
    mock_pgexecute.assert_called_with(
        "b_dbname",
        "b_user",
        "very_secure",
        "b_host",
        "5435",
        "",
        notify_callback,
        application_name="pgcli",
        connect_timeout="30",
    )
    del os.environ["PGPASSWORD"]
    del os.environ["PGSERVICEFILE"]


def test_ssl_db_uri(tmpdir):
    with mock.patch.object(PGCli, "connect") as mock_connect:
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        cli.connect_uri(
            "postgres://bar%5E:%5Dfoo@baz.com/testdb%5B?sslmode=verify-full&sslcert=m%79.pem&sslkey=my-key.pem&sslrootcert=c%61.pem"
        )
    mock_connect.assert_called_with(
        database="testdb[",
        host="baz.com",
        user="bar^",
        passwd="]foo",
        sslmode="verify-full",
        sslcert="my.pem",
        sslkey="my-key.pem",
        sslrootcert="ca.pem",
    )


def test_port_db_uri(tmpdir):
    with mock.patch.object(PGCli, "connect") as mock_connect:
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        cli.connect_uri("postgres://bar:foo@baz.com:2543/testdb")
    mock_connect.assert_called_with(database="testdb", host="baz.com", user="bar", passwd="foo", port="2543")


def test_multihost_db_uri(tmpdir):
    with mock.patch.object(PGCli, "connect") as mock_connect:
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        cli.connect_uri("postgres://bar:foo@baz1.com:2543,baz2.com:2543,baz3.com:2543/testdb")
    mock_connect.assert_called_with(
        database="testdb",
        host="baz1.com,baz2.com,baz3.com",
        user="bar",
        passwd="foo",
        port="2543,2543,2543",
    )


def test_application_name_db_uri(tmpdir):
    with mock.patch.object(PGExecute, "__init__") as mock_pgexecute:
        mock_pgexecute.return_value = None
        cli = PGCli(pgclirc_file=str(tmpdir.join("rcfile")))
        cli.connect_uri("postgres://bar@baz.com/?application_name=cow")
    mock_pgexecute.assert_called_with("bar", "bar", "", "baz.com", "", "", notify_callback, application_name="cow", connect_timeout="30")


@pytest.mark.parametrize(
    "duration_in_seconds,words",
    [
        (0, "0 seconds"),
        (0.0009, "0.001 second"),
        (0.0005, "0.001 second"),
        (0.0004, "0.0 second"),  # not perfect, but will do
        (0.2, "0.2 second"),
        (1, "1 second"),
        (1.4, "1 second"),
        (2, "2 seconds"),
        (3.4, "3 seconds"),
        (60, "1 minute"),
        (61, "1 minute 1 second"),
        (123, "2 minutes 3 seconds"),
        (124.4, "2 minutes 4 seconds"),
        (3600, "1 hour"),
        (7235, "2 hours 35 seconds"),
        (9005, "2 hours 30 minutes 5 seconds"),
        (9006.7, "2 hours 30 minutes 6 seconds"),
        (86401, "24 hours 1 second"),
    ],
)
def test_duration_in_words(duration_in_seconds, words):
    assert duration_in_words(duration_in_seconds) == words


@pytest.mark.parametrize(
    "transaction_indicator,expected",
    [
        ("*", "*testuser"),  # valid transaction
        ("!", "!testuser"),  # failed transaction
        ("?", "?testuser"),  # connection closed
        ("", "testuser"),  # idle
    ],
)
def test_get_prompt_with_transaction_status(transaction_indicator, expected):
    cli = PGCli()
    cli.pgexecute = mock.MagicMock()
    cli.pgexecute.user = "testuser"
    cli.pgexecute.dbname = "testdb"
    cli.pgexecute.host = "localhost"
    cli.pgexecute.short_host = "localhost"
    cli.pgexecute.port = 5432
    cli.pgexecute.pid = 12345
    cli.pgexecute.superuser = False
    cli.pgexecute.transaction_indicator = transaction_indicator

    result = cli.get_prompt("\\T\\u")
    assert result == expected


def test_get_prompt_transaction_status_in_full_prompt():
    cli = PGCli()
    cli.pgexecute = mock.MagicMock()
    cli.pgexecute.user = "user"
    cli.pgexecute.dbname = "mydb"
    cli.pgexecute.host = "db.example.com"
    cli.pgexecute.short_host = "db.example.com"
    cli.pgexecute.port = 5432
    cli.pgexecute.pid = 12345
    cli.pgexecute.superuser = False
    cli.pgexecute.transaction_indicator = "*"

    result = cli.get_prompt("\\T\\u@\\h:\\d> ")
    assert result == "*user@db.example.com:mydb> "


@dbtest
def test_notifications(executor):
    run(executor, "listen chan1")

    with mock.patch("pgcli.main.click.secho") as mock_secho:
        run(executor, "notify chan1, 'testing1'")
        mock_secho.assert_called()
        arg = mock_secho.call_args_list[0].args[0]
    assert re.match(
        r'Notification received on channel "chan1" \(PID \d+\):\ntesting1',
        arg,
    )

    run(executor, "unlisten chan1")

    with mock.patch("pgcli.main.click.secho") as mock_secho:
        run(executor, "notify chan1, 'testing2'")
        mock_secho.assert_not_called()


def test_edit_named_query():
    """Test \\ne edits/creates a named query via the external editor."""
    from pgspecial.namedqueries import NamedQueries

    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = os.path.join(tmpdir, "config")
        with open(config_file, "w") as f:
            f.write("[main]\n")
            f.write(f"log_file = {os.path.join(tmpdir, 'pgcli.log')}\n")

        cli = PGCli(pgclirc_file=config_file)

        # Create a new named query (editor returns SQL, no error).
        with mock.patch("pgcli.main.special.open_external_editor", return_value=("select 1", None)):
            out = cli.edit_named_query("foo")
        assert "Created" in out[0][3]
        assert NamedQueries.instance.get("foo") == "select 1"

        # Update the existing one.
        with mock.patch("pgcli.main.special.open_external_editor", return_value=("select 2", None)):
            out = cli.edit_named_query("foo")
        assert "Saved" in out[0][3]
        assert NamedQueries.instance.get("foo") == "select 2"

        # No changes -> not re-saved.
        with mock.patch("pgcli.main.special.open_external_editor", return_value=("select 2", None)):
            out = cli.edit_named_query("foo")
        assert "no changes" in out[0][3]

        # Empty editor result -> not saved, previous value kept.
        with mock.patch("pgcli.main.special.open_external_editor", return_value=("", None)):
            out = cli.edit_named_query("foo")
        assert "not saved" in out[0][3]
        assert NamedQueries.instance.get("foo") == "select 2"

        # Editor reported an error -> surfaced, nothing saved.
        with mock.patch("pgcli.main.special.open_external_editor", return_value=(None, "boom")):
            out = cli.edit_named_query("foo")
        assert out[0][3] == "boom"

        # Missing name -> usage message.
        out = cli.edit_named_query("")
        assert "Usage" in out[0][3]


def test_get_editor_precedence():
    """PSQL_EDITOR wins over EDITOR/VISUAL, like psql; None when nothing is set."""
    env = {"PSQL_EDITOR": "psqled", "EDITOR": "myedit", "VISUAL": "myvisual"}
    with mock.patch.dict(os.environ, env, clear=False):
        assert get_editor() == "psqled"

    # PSQL_EDITOR unset -> fall back to EDITOR.
    with mock.patch.dict(os.environ, {"EDITOR": "myedit", "VISUAL": "myvisual"}, clear=True):
        assert get_editor() == "myedit"

    # Only VISUAL set.
    with mock.patch.dict(os.environ, {"VISUAL": "myvisual"}, clear=True):
        assert get_editor() == "myvisual"

    # Nothing set -> None, so click uses its platform default.
    with mock.patch.dict(os.environ, {}, clear=True):
        assert get_editor() is None


def _cli_conn_target(argv, tmpdir):
    """Run cli() with argv and report which connect_* path it took."""
    rc = tmpdir.join("rcfile")
    rc.write("[main]\n")
    runner = CliRunner()
    with (
        mock.patch.object(PGCli, "connect_uri", side_effect=RuntimeError("stop")) as mock_uri,
        mock.patch.object(PGCli, "connect_dsn", side_effect=RuntimeError("stop")) as mock_dsn,
        mock.patch.object(PGCli, "connect", side_effect=RuntimeError("stop")) as mock_plain,
    ):
        runner.invoke(cli, argv + ["--pgclirc", str(rc)])
    if mock_uri.called:
        return "uri", mock_uri.call_args
    if mock_dsn.called:
        return "dsn", mock_dsn.call_args
    if mock_plain.called:
        return "plain", mock_plain.call_args
    return "none", None


def test_list_databases_keeps_uri(tmpdir):
    """-l must not discard a connection URI: doing so fell back to a local
    socket connection as the OS user."""
    uri = "postgresql://someuser@somehost:6000/somedb"
    path, call = _cli_conn_target([uri, "-l"], tmpdir)
    assert path == "uri"
    assert call.args[0] == uri


def test_list_databases_keeps_kv_conninfo(tmpdir):
    """Same for a key=value conninfo string, which carries sslmode and friends."""
    kv = "host=somehost port=6000 user=someuser dbname=somedb sslmode=verify-ca"
    path, call = _cli_conn_target([kv, "-l"], tmpdir)
    assert path == "dsn"
    assert call.args[0] == kv


def test_ping_keeps_uri(tmpdir):
    """--ping handles connection strings the same way as -l."""
    uri = "postgresql://someuser@somehost:6000/somedb"
    path, call = _cli_conn_target([uri, "--ping"], tmpdir)
    assert path == "uri"
    assert call.args[0] == uri


def test_list_databases_conn_string_without_dbname_gets_postgres(tmpdir):
    """A connection string naming no database gets "postgres" for the listing,
    instead of libpq defaulting to the OS user name."""
    kv = "host=somehost user=someuser sslmode=verify-ca"
    path, call = _cli_conn_target([kv, "-l"], tmpdir)
    assert path == "dsn"
    assert conninfo_to_dict(call.args[0])["dbname"] == "postgres"
    assert conninfo_to_dict(call.args[0])["sslmode"] == "verify-ca"  # rest preserved


def test_list_databases_keeps_plain_dbname(tmpdir):
    """psql -l connects to the named database and lists from there
    (psql -l nonexistent fails with "database does not exist"), so a
    plain db name is kept."""
    path, call = _cli_conn_target(["mydb", "-l"], tmpdir)
    assert path == "plain"
    assert call.args[0] == "mydb"


def test_list_databases_no_dbname_gets_postgres(tmpdir):
    """With no database at all, -l connects to "postgres"."""
    path, call = _cli_conn_target(["-l"], tmpdir)
    assert path == "plain"
    assert call.args[0] == "postgres"


def _effective_connect_timeout(tmpdir, cli_timeout=None, dsn_timeout=None, env=None, cfgval=None):
    """The connect_timeout that actually reaches the connection."""
    rc = str(tmpdir.join("rcfile"))
    with open(rc, "w") as f:
        f.write("[main]\n" + (f"connect_timeout = {cfgval}\n" if cfgval else ""))
    environ = {k: v for k, v in os.environ.items() if k != "PGCONNECT_TIMEOUT"}
    if env:
        environ["PGCONNECT_TIMEOUT"] = env
    with mock.patch.dict(os.environ, environ, clear=True):
        cli_obj = PGCli(pgclirc_file=rc, connect_timeout=cli_timeout)
        dsn = "postgresql://u@h:5432/db" + (f"?connect_timeout={dsn_timeout}" if dsn_timeout else "")
        captured = {}

        def fake(*a, **k):
            captured["dsn"] = k.get("dsn") or (a[5] if len(a) > 5 else None)
            captured["kwargs"] = k
            raise RuntimeError("stop")

        # connect() turns a failed connection into sys.exit(1); let it.
        with mock.patch("pgcli.main.PGExecute", side_effect=fake), pytest.raises(SystemExit):
            cli_obj.connect(dsn=dsn, host="h", port="5432", user="u", database="db")
        from_kwargs = captured.get("kwargs", {}).get("connect_timeout")
        return from_kwargs or conninfo_to_dict(captured.get("dsn") or "").get("connect_timeout")


DSN_WITH_TIMEOUT = "postgresql://u@h:5432/db?connect_timeout=15"
DSN_PLAIN = "postgresql://u@h:5432/db"


@pytest.mark.parametrize(
    "explicit, dsn, kwargs, env, expected, why",
    [
        (None, DSN_PLAIN, {}, None, 30, "nothing else set, so the config default applies"),
        (None, DSN_WITH_TIMEOUT, {}, None, None, "the connection string already says so"),
        (None, DSN_PLAIN, {"connect_timeout": "9"}, None, None, "the caller already says so"),
        (None, DSN_PLAIN, {}, "7", None, "libpq reads $PGCONNECT_TIMEOUT itself"),
        (None, DSN_WITH_TIMEOUT, {}, "7", None, "the connection string beats the environment"),
        (3, DSN_WITH_TIMEOUT, {}, "7", 3, "--timeout beats everything"),
        (0, DSN_WITH_TIMEOUT, {}, None, 0, "--timeout 0 is meaningful, not unset"),
        (None, None, {}, None, 30, "no dsn at all"),
    ],
)
def test_get_connect_timeout(explicit, dsn, kwargs, env, expected, why):
    environ = {k: v for k, v in os.environ.items() if k != "PGCONNECT_TIMEOUT"}
    if env:
        environ["PGCONNECT_TIMEOUT"] = env
    with mock.patch.dict(os.environ, environ, clear=True):
        assert get_connect_timeout(explicit, dsn, kwargs, 30) == expected, why


def test_connect_timeout_config_default_reaches_the_connection(tmpdir):
    """The helper is actually wired into connect(): libpq's own default of 0
    waits until the OS gives up, which takes minutes."""
    assert _effective_connect_timeout(tmpdir) == "30"


def test_connect_timeout_config_value_used(tmpdir):
    assert _effective_connect_timeout(tmpdir, cfgval=45) == "45"


def test_connect_timeout_cli_reaches_the_connection(tmpdir):
    assert _effective_connect_timeout(tmpdir, cli_timeout=3, dsn_timeout=15, env="7") == "3"


def test_connect_timeout_config_value_must_be_a_number(tmpdir):
    """A typo in the config is reported instead of being silently ignored."""
    rc = str(tmpdir.join("rcfile"))
    with open(rc, "w") as f:
        f.write("[main]\nconnect_timeout = soon\n")
    with pytest.raises(ValueError):
        PGCli(pgclirc_file=rc)
