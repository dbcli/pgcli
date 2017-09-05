# -*- coding: utf-8
from __future__ import unicode_literals

import re
import pexpect


def expect_exact(context, expected, timeout):
    try:
        context.cli.expect_exact(expected, timeout=timeout)
    except:
        # Strip color codes out of the output.
        actual = re.sub(r'\x1b\[([0-9A-Za-z;?])+[m|K]?', '', context.cli.before)
        raise Exception('Expected:\n---\n{0!r}\n---\n\nActual:\n---\n{1!r}\n---'.format(
            expected,
            actual))


def expect_pager(context, expected, timeout):
    expect_exact(context, "{0}\r\n{1}{0}\r\n".format(
        context.conf['pager_boundary'], expected), timeout=timeout)


def run_cli(context, run_args=None):
    """Run the process using pexpect."""
    run_args = run_args or []
    cli_cmd = context.conf.get('cli_command')
    cmd_parts = [cli_cmd] + run_args
    cmd = ' '.join(cmd_parts)
    context.cli = pexpect.spawnu(cmd, cwd=context.package_root)
    context.exit_sent = False
    context.currentdb = context.conf['dbname']


def wait_prompt(context):
    """Make sure prompt is displayed."""
    expect_exact(context, '{0}> '.format(context.conf['dbname']), timeout=5)
