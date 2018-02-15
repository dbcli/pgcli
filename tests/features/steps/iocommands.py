# -*- coding: utf-8
from __future__ import unicode_literals
import os
import os.path
import wrappers

from behave import when, then


@when('we start external editor providing a file name')
def step_edit_file(context):
    """Edit file with external editor."""
    context.editor_file_name = os.path.join(
        context.package_root, 'test_file_{0}.sql'.format(context.conf['vi']))
    if os.path.exists(context.editor_file_name):
        os.remove(context.editor_file_name)
    context.cli.sendline('\e {0}'.format(
        os.path.basename(context.editor_file_name)))
    wrappers.expect_exact(
        context, 'Entering Ex mode.  Type "visual" to go to Normal mode.', timeout=2)
    wrappers.expect_exact(context, ':', timeout=2)


@when('we type sql in the editor')
def step_edit_type_sql(context):
    context.cli.sendline('i')
    context.cli.sendline('select * from abc')
    context.cli.sendline('.')
    wrappers.expect_exact(context, ':', timeout=2)


@when('we exit the editor')
def step_edit_quit(context):
    context.cli.sendline('x')
    wrappers.expect_exact(context, "written", timeout=2)


@then('we see the sql in prompt')
def step_edit_done_sql(context):
    for match in 'select * from abc'.split(' '):
        wrappers.expect_exact(context, match, timeout=1)
    # Cleanup the command line.
    context.cli.sendcontrol('c')
    # Cleanup the edited file.
    if context.editor_file_name and os.path.exists(context.editor_file_name):
        os.remove(context.editor_file_name)


@when(u'we tee output')
def step_tee_ouptut(context):
    context.tee_file_name = os.path.join(
        context.package_root, 'tee_file_{0}.sql'.format(context.conf['vi']))
    if os.path.exists(context.tee_file_name):
        os.remove(context.tee_file_name)
    context.cli.sendline('\o {0}'.format(
        os.path.basename(context.tee_file_name)))
    wrappers.expect_exact(
        context, context.conf['pager_boundary'] + '\r\n', timeout=5)
    wrappers.expect_exact(context, "Writing to file", timeout=5)
    wrappers.expect_exact(
        context, context.conf['pager_boundary'] + '\r\n', timeout=5)
    wrappers.expect_exact(context, "Time", timeout=5)


@when(u'we query "select 123456"')
def step_query_select_123456(context):
    context.cli.sendline('select 123456')


@when(u'we stop teeing output')
def step_notee_output(context):
    context.cli.sendline('\o')
    wrappers.expect_exact(context, "Time", timeout=5)


@then(u'we see 123456 in tee output')
def step_see_123456_in_ouput(context):
    with open(context.tee_file_name) as f:
        assert '123456' in f.read()
    if os.path.exists(context.tee_file_name):
        os.remove(context.tee_file_name)
    context.atprompt = True
