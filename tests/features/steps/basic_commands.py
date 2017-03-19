# -*- coding: utf-8
"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""
from __future__ import unicode_literals

import pexpect

from behave import when
import wrappers


@when('we run pgcli')
def step_run_cli(context):
    """
    Run the process using pexpect.
    """
    context.cli = pexpect.spawnu('pgcli')
    context.exit_sent = False


@when('we wait for prompt')
def step_wait_prompt(context):
    """
    Make sure prompt is displayed.
    """
    wrappers.expect_exact(context, '{0}> '.format(context.conf['dbname']), timeout=5)


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
