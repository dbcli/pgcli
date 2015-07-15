# -*- coding: utf-8 -*-
"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""
from __future__ import unicode_literals

import pip
import pexpect

from behave import given, when, then


@given('we have pgcli installed')
def step_install_cli(_):
    """
    Check that pgcli is in installed modules.
    """
    dists = set([di.key for di in pip.get_installed_distributions()])
    assert 'pgcli' in dists


@when('we run pgcli')
def step_run_cli(context):
    """
    Run the process using pexpect.
    """
    context.cli = pexpect.spawnu('pgcli')


@when('we wait for prompt')
def step_wait_prompt(context):
    """
    Make sure prompt is displayed.
    """
    context.cli.expect('{0}> '.format(context.conf['dbname']))


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


@then('pgcli exits')
def step_wait_exit(context):
    """
    Make sure the cli exits.
    """
    context.cli.expect(pexpect.EOF)


@then('we see pgcli prompt')
def step_see_prompt(context):
    """
    Wait to see the prompt.
    """
    context.cli.expect('{0}> '.format(context.conf['dbname']))


@then('we see help output')
def step_see_help(context):
    for expected_line in context.fixture_data['help_commands.txt']:
        try:
            context.cli.expect_exact(expected_line, timeout=1)
        except Exception:
            raise Exception('Expected: ' + expected_line.strip() + '!')
