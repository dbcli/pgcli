import re
import pexpect
from pgcli.main import COLOR_CODE_REGEX
import textwrap

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO


def expect_exact(context, expected, timeout):
    timedout = False
    try:
        context.cli.expect_exact(expected, timeout=timeout)
    except pexpect.TIMEOUT:
        timedout = True
    if timedout:
        # Strip color codes out of the output.
        actual = re.sub(r"\x1b\[([0-9A-Za-z;?])+[m|K]?", "", context.cli.before)
        raise Exception(
            textwrap.dedent(
                """\
                Expected:
                ---
                {0!r}
                ---
                Actual:
                ---
                {1!r}
                ---
                Full log:
                ---
                {2!r}
                ---
            """
            ).format(expected, actual, context.logfile.getvalue())
        )


def expect_pager(context, expected, timeout):
    formatted = expected if isinstance(expected, list) else [expected]
    formatted = [
        f"{context.conf['pager_boundary']}\r\n{t}{context.conf['pager_boundary']}\r\n"
        for t in formatted
    ]

    expect_exact(
        context,
        formatted,
        timeout=timeout,
    )


def run_cli(context, run_args=None, prompt_check=True, currentdb=None):
    """Run the process using pexpect."""
    run_args = run_args or []
    cli_cmd = context.conf.get("cli_command")
    cmd_parts = [cli_cmd] + run_args
    cmd = " ".join(cmd_parts)
    context.cli = pexpect.spawnu(cmd, cwd=context.package_root)
    context.logfile = StringIO()
    context.cli.logfile = context.logfile
    context.exit_sent = False
    context.currentdb = currentdb or context.conf["dbname"]
    context.cli.sendline(r"\pset pager always")
    if prompt_check:
        wait_prompt(context)


def wait_prompt(context):
    """Make sure prompt is displayed."""
    expect_exact(context, "{0}> ".format(context.conf["dbname"]), timeout=5)
