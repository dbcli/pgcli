# -*- coding: utf-8
"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""
from __future__ import unicode_literals

import tempfile

from behave import when
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
    with tempfile.NamedTemporaryFile() as f:
        f.write(b'\?')
        f.flush()
        context.cli.sendline('\i {0}'.format(f.name))
        wrappers.expect_exact(
            context, context.conf['pager_boundary'] + '\r\n', timeout=5)
