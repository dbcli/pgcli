"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""

from behave import when, then
import wrappers


@when('we send "show help" command')
def step_send_help_command(context):
    context.cli.sendline("show help")


@then("we see the pgbouncer help output")
def see_pgbouncer_help(context):
    wrappers.expect_exact(
        context,
        "SHOW HELP|CONFIG|DATABASES|POOLS|CLIENTS|SERVERS|USERS|VERSION",
        timeout=3,
    )
