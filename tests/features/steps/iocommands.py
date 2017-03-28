# -*- coding: utf-8
from __future__ import unicode_literals
import os
import re
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
    wrappers.expect_exact(context, 'Entering Ex mode.  Type "visual" to go to Normal mode.', timeout=2)
    wrappers.expect_exact(context, '\r\n:', timeout=2)


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
    colored_expr = re.compile('select(.+?)\*(.+?)from(.+?)abc')
    wrappers.expect(context, colored_expr, timeout=2)
    # Cleanup the command line.
    context.cli.sendcontrol('u')
    # Cleanup the edited file.
    if context.editor_file_name and os.path.exists(context.editor_file_name):
        os.remove(context.editor_file_name)
