# -*- coding: utf-8
"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""
from __future__ import unicode_literals, print_function

import tempfile

from behave import when, then
from textwrap import dedent
import wrappers


@when('we run dbcli')
def step_run_cli(context):
    wrappers.run_cli(context)


@when('we wait for prompt')
def step_wait_prompt(context):
    wrappers.wait_prompt(context)


@when('we send "ctrl + d"')
def step_ctrl_d(context):
    """
    Send Ctrl + D to hopefully exit.
    """
    # turn off pager before exiting
    context.cli.sendline('\pset pager off')
    wrappers.wait_prompt(context)
    context.cli.sendcontrol('d')
    context.exit_sent = True


@when('we send "\?" command')
def step_send_help(context):
    """
    Send \? to see help.
    """
    context.cli.sendline('\?')


@when(u'we send source command')
def step_send_source_command(context):
    context.tmpfile_sql_help = tempfile.NamedTemporaryFile(prefix='pgcli_')
    context.tmpfile_sql_help.write(b'\?')
    context.tmpfile_sql_help.flush()
    context.cli.sendline('\i {0}'.format(context.tmpfile_sql_help.name))
    wrappers.expect_exact(
        context, context.conf['pager_boundary'] + '\r\n', timeout=5)


@when(u'we run query to check application_name')
def step_check_application_name(context):
    context.cli.sendline(
        "SELECT 'found' FROM pg_stat_activity WHERE application_name = 'pgcli' HAVING COUNT(*) > 0;"
    )


@then(u'we see found')
def step_see_found(context):
    wrappers.expect_exact(
        context,
        context.conf['pager_boundary'] + '\r' + dedent('''
            +------------+\r
            | ?column?   |\r
            |------------|\r
            | found      |\r
            +------------+\r
            SELECT 1\r
        ''') + context.conf['pager_boundary'],
        timeout=5
    )


@then(u'we confirm the destructive warning')
def step_confirm_destructive_command(context):
    """Confirm destructive command."""
    wrappers.expect_exact(
        context, 'You\'re about to run a destructive command.\r\nDo you want to proceed? (y/n):', timeout=2)
    context.cli.sendline('y')
