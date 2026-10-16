import time
from unittest.mock import patch

from pgcli.main import PGCli
from utils import dbtest


def _leave_query_unread(executor):
    """Put the connection where a second Ctrl-C leaves it.

    psycopg handles the first Ctrl-C by sending a cancel and then reading the
    server's answer; a second Ctrl-C during that cleanup (easy over an SSH
    tunnel, where it takes a round trip or two) interrupts it, so the query is
    still running on the server and its answer is never read.
    """
    executor.conn.pgconn.send_query(b"select pg_sleep(30)")
    raise KeyboardInterrupt


@dbtest
def test_double_ctrl_c_does_not_leave_the_connection_busy(executor):
    cli = PGCli(pgexecute=executor)
    start = time.monotonic()

    with patch.object(cli, "_evaluate_command", side_effect=lambda text: _leave_query_unread(executor)):
        cli.execute_command("select pg_sleep(30)")
    output, query = cli._evaluate_command("select 40 + 2 as answer")

    # Without the recovery every later statement failed with "another command
    # is already in progress".
    assert query.successful
    assert any("42" in line for line in output)
    # The query was cancelled on the server, not waited out.
    assert time.monotonic() - start < 10


@dbtest
def test_connection_still_busy_after_the_cancel_is_closed_then_reopened(executor):
    cli = PGCli(pgexecute=executor)
    cli.auto_retry_closed_connection = True

    with (
        patch.object(executor, "_drain_results", return_value=False),
        patch.object(cli, "_evaluate_command", side_effect=lambda text: _leave_query_unread(executor)),
    ):
        cli.execute_command("select pg_sleep(30)")
    assert executor.conn.closed

    # The next statement goes through pgcli's usual closed-connection path.
    cli.execute_command("select 1")
    assert not executor.conn.closed
    output, query = cli._evaluate_command("select 40 + 2 as answer")
    assert query.successful


def _still_running(connection, pid):
    """Whether backend `pid` is still running its query, given 2s to stop."""
    for _ in range(20):
        with connection.cursor() as cur:
            cur.execute("select state from pg_stat_activity where pid = %s", (pid,))
            row = cur.fetchone()
        if row is None or row[0] != "active":
            return False
        time.sleep(0.1)
    return True


@dbtest
def test_another_ctrl_c_during_the_recovery_closes_the_connection(executor, connection):
    cli = PGCli(pgexecute=executor)
    pid = executor.conn.info.backend_pid

    with (
        patch.object(executor, "recover_from_interrupt", side_effect=KeyboardInterrupt),
        patch.object(cli, "_evaluate_command", side_effect=lambda text: _leave_query_unread(executor)),
    ):
        cli.execute_command("select pg_sleep(30)")

    assert executor.conn.closed
    # Closing alone would leave the sleep running on the server.
    assert not _still_running(connection, pid)


@dbtest
def test_idle_connection_is_left_alone(executor):
    # Ctrl-C after the query finished (say, while printing) must not cost the
    # session its settings.
    executor.conn.execute("set application_name = 'kept'")
    conn = executor.conn

    assert executor.recover_from_interrupt() == "idle"
    assert executor.conn is conn
    with executor.conn.cursor() as cur:
        cur.execute("show application_name")
        assert cur.fetchone()[0] == "kept"
