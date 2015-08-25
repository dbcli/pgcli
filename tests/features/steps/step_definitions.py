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
    context.exit_sent = False


@when('we wait for prompt')
def step_wait_prompt(context):
    """
    Make sure prompt is displayed.
    """
    context.cli.expect('{0}> '.format(context.conf['dbname']), timeout=5)


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


@when('we create table')
def step_create_table(context):
    """
    Send create table.
    """
    context.cli.sendline('create table a(x text);')


@when('we insert into table')
def step_insert_into_table(context):
    """
    Send insert into table.
    """
    context.cli.sendline('''insert into a(x) values('xxx');''')


@when('we update table')
def step_update_table(context):
    """
    Send insert into table.
    """
    context.cli.sendline('''update a set x = 'yyy' where x = 'xxx';''')


@when('we select from table')
def step_select_from_table(context):
    """
    Send select from table.
    """
    context.cli.sendline('select * from a;')


@when('we delete from table')
def step_delete_from_table(context):
    """
    Send deete from table.
    """
    context.cli.sendline('''delete from a where x = 'yyy';''')


@when('we drop table')
def step_drop_table(context):
    """
    Send drop table.
    """
    context.cli.sendline('drop table a;')


@when('we connect to test database')
def step_db_connect_test(context):
    """
    Send connect to database.
    """
    db_name = context.conf['dbname']
    context.cli.sendline('\connect {0}'.format(db_name))


@when('we connect to postgres')
def step_db_connect_postgres(context):
    """
    Send connect to database.
    """
    context.cli.sendline('\connect postgres')


@then('pgcli exits')
def step_wait_exit(context):
    """
    Make sure the cli exits.
    """
    context.cli.expect(pexpect.EOF, timeout=5)


@then('we see pgcli prompt')
def step_see_prompt(context):
    """
    Wait to see the prompt.
    """
    context.cli.expect('{0}> '.format(context.conf['dbname']), timeout=5)


@then('we see help output')
def step_see_help(context):
    for expected_line in context.fixture_data['help_commands.txt']:
        try:
            context.cli.expect_exact(expected_line, timeout=1)
        except Exception:
            raise Exception('Expected: ' + expected_line.strip() + '!')


@then('we see database created')
def step_see_db_created(context):
    """
    Wait to see create database output.
    """
    context.cli.expect_exact('CREATE DATABASE', timeout=2)


@then('we see database dropped')
def step_see_db_dropped(context):
    """
    Wait to see drop database output.
    """
    context.cli.expect_exact('DROP DATABASE', timeout=2)


@then('we see database connected')
def step_see_db_connected(context):
    """
    Wait to see drop database output.
    """
    context.cli.expect_exact('You are now connected to database', timeout=2)


@then('we see table created')
def step_see_table_created(context):
    """
    Wait to see create table output.
    """
    context.cli.expect_exact('CREATE TABLE', timeout=2)


@then('we see record inserted')
def step_see_record_inserted(context):
    """
    Wait to see insert output.
    """
    context.cli.expect_exact('INSERT 0 1', timeout=2)


@then('we see record updated')
def step_see_record_updated(context):
    """
    Wait to see update output.
    """
    context.cli.expect_exact('UPDATE 1', timeout=2)


@then('we see data selected')
def step_see_data_selected(context):
    """
    Wait to see select output.
    """
    context.cli.expect_exact('yyy', timeout=1)
    context.cli.expect_exact('SELECT 1', timeout=1)


@then('we see record deleted')
def step_see_data_deleted(context):
    """
    Wait to see delete output.
    """
    context.cli.expect_exact('DELETE 1', timeout=2)


@then('we see table dropped')
def step_see_table_dropped(context):
    """
    Wait to see drop output.
    """
    context.cli.expect_exact('DROP TABLE', timeout=2)
