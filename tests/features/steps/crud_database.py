# -*- coding: utf-8 -*-
"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""
from __future__ import unicode_literals

import pexpect

import wrappers
from behave import when, then


@when('we create database')
def step_db_create(context):
    """
    Send create database.
    """
    context.cli.sendline('create database {0};'.format(
        context.conf['dbname_tmp']))

    context.response = {
        'database_name': context.conf['dbname_tmp']
    }


@when('we drop database')
def step_db_drop(context):
    """
    Send drop database.
    """
    context.cli.sendline('drop database {0};'.format(
        context.conf['dbname_tmp']))


@when('we connect to test database')
def step_db_connect_test(context):
    """
    Send connect to database.
    """
    db_name = context.conf['dbname']
    context.cli.sendline('\\connect {0}'.format(db_name))


@when('we connect to postgres')
def step_db_connect_postgres(context):
    """
    Send connect to database.
    """
    context.cli.sendline('\\connect postgres')


@then('pgcli exits')
def step_wait_exit(context):
    """
    Make sure the cli exits.
    """
    wrappers.expect_exact(context, pexpect.EOF, timeout=5)


@then('we see pgcli prompt')
def step_see_prompt(context):
    """
    Wait to see the prompt.
    """
    wrappers.expect_exact(context, '{0}> '.format(context.conf['dbname']), timeout=5)


@then('we see help output')
def step_see_help(context):
    for expected_line in context.fixture_data['help_commands.txt']:
        wrappers.expect_exact(context, expected_line, timeout=1)


@then('we see database created')
def step_see_db_created(context):
    """
    Wait to see create database output.
    """
    wrappers.expect_exact(context, 'CREATE DATABASE', timeout=2)


@then('we see database dropped')
def step_see_db_dropped(context):
    """
    Wait to see drop database output.
    """
    wrappers.expect_exact(context, 'DROP DATABASE', timeout=2)


@then('we see database connected')
def step_see_db_connected(context):
    """
    Wait to see drop database output.
    """
    wrappers.expect_exact(context, 'You are now connected to database', timeout=2)
