# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pip
import pexpect

from behave import given, when, then

@given('we have pgcli installed')
def step_impl(context):
    ds = set([di.key for di in pip.get_installed_distributions()])
    assert 'pgcli' in ds

@when('we run pgcli')
def step_impl(context):
    context.cli = pexpect.spawnu('pgcli')


@when('we wait for prompt')
def step_impl(context):
    context.cli.expect('{0}> '.format(context.conf['dbname']))

@when('we send "ctrl + d"')
def step_impl(context):
    context.cli.sendcontrol('d')
    context.exit_sent = True

@then('pgcli exits')
def step_impl(context):
    context.cli.expect(pexpect.EOF)

@then('we see pgcli prompt')
def step_impl(context):
    context.cli.expect('{0}> '.format(context.conf['dbname']))
