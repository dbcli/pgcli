# -*- coding: utf-8
from __future__ import unicode_literals
import os
import wrappers

from behave import when, then


@when('we start external editor providing a file name')
def step_edit_file(context):
    """
    Edit file with external editor.
    """
    context.editor_file_name = 'test_file_{0}.sql'.format(context.conf['vi'])
    if os.path.exists(context.editor_file_name):
        os.remove(context.editor_file_name)
    context.cli.sendline('\e {0}'.format(context.editor_file_name))
    wrappers.expect_exact(context, 'nano', timeout=2)


@when('we type sql in the editor')
def step_edit_type_sql(context):
    context.cli.sendline('select * from abc')
    # Write the file.
    context.cli.sendcontrol('o')
    # Confirm file name sending "enter".
    context.cli.sendcontrol('m')


@when('we exit the editor')
def step_edit_quit(context):
    context.cli.sendcontrol('x')


@then('we see the sql in prompt')
def step_edit_done_sql(context):
    wrappers.expect_exact(context, 'select * from abc', timeout=2)
    # Cleanup the command line.
    context.cli.sendcontrol('u')
    # Cleanup the edited file.
    if context.editor_file_name and os.path.exists(context.editor_file_name):
        os.remove(context.editor_file_name)
