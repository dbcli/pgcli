"""
Steps for behavioral style tests are defined in this module.
Each step is defined by the string decorating it.
This string is used to call the step in "*.feature" file.
"""

from behave import when, then
from textwrap import dedent
import wrappers


INITIAL_DATA = "xxx"
UPDATED_DATA = "yyy"


@when("we create table")
def step_create_table(context):
    """
    Send create table.
    """
    context.cli.sendline("create table a(x text);")


@when("we insert into table")
def step_insert_into_table(context):
    """
    Send insert into table.
    """
    context.cli.sendline(f"""insert into a(x) values('{INITIAL_DATA}');""")


@when("we update table")
def step_update_table(context):
    """
    Send insert into table.
    """
    context.cli.sendline(f"""update a set x = '{UPDATED_DATA}' where x = '{INITIAL_DATA}';""")


@when("we select from table")
def step_select_from_table(context):
    """
    Send select from table.
    """
    context.cli.sendline("select * from a;")


@when("we delete from table")
def step_delete_from_table(context):
    """
    Send deete from table.
    """
    context.cli.sendline(f"""delete from a where x = '{UPDATED_DATA}';""")


@when("we drop table")
def step_drop_table(context):
    """
    Send drop table.
    """
    context.cli.sendline("drop table a;")


@when("we alter the table")
def step_alter_table(context):
    """
    Alter the table by adding a column.
    """
    context.cli.sendline("""alter table a add column y varchar;""")


@when("we begin transaction")
def step_begin_transaction(context):
    """
    Begin transaction
    """
    context.cli.sendline("begin;")


@when("we rollback transaction")
def step_rollback_transaction(context):
    """
    Rollback transaction
    """
    context.cli.sendline("rollback;")


@then("we see table created")
def step_see_table_created(context):
    """
    Wait to see create table output.
    """
    wrappers.expect_pager(context, "CREATE TABLE\r\n", timeout=2)


@then("we see record inserted")
def step_see_record_inserted(context):
    """
    Wait to see insert output.
    """
    wrappers.expect_pager(context, "INSERT 0 1\r\n", timeout=2)


@then("we see record updated")
def step_see_record_updated(context):
    """
    Wait to see update output.
    """
    wrappers.expect_pager(context, "UPDATE 1\r\n", timeout=2)


@then("we see data selected: {data}")
def step_see_data_selected(context, data):
    """
    Wait to see select output with initial or updated data.
    """
    x = UPDATED_DATA if data == "updated" else INITIAL_DATA
    wrappers.expect_pager(
        context,
        dedent(
            f"""\
            +-----+\r
            | x   |\r
            |-----|\r
            | {x} |\r
            +-----+\r
            SELECT 1\r
        """
        ),
        timeout=1,
    )


@then("we see select output without data")
def step_see_no_data_selected(context):
    """
    Wait to see select output without data.
    """
    wrappers.expect_pager(
        context,
        dedent(
            """\
            +---+\r
            | x |\r
            |---|\r
            +---+\r
            SELECT 0\r
        """
        ),
        timeout=1,
    )


@then("we see record deleted")
def step_see_data_deleted(context):
    """
    Wait to see delete output.
    """
    wrappers.expect_pager(context, "DELETE 1\r\n", timeout=2)


@then("we see table dropped")
def step_see_table_dropped(context):
    """
    Wait to see drop output.
    """
    wrappers.expect_pager(context, "DROP TABLE\r\n", timeout=2)


@then("we see transaction began")
def step_see_transaction_began(context):
    """
    Wait to see transaction began.
    """
    wrappers.expect_pager(context, "BEGIN\r\n", timeout=2)


@then("we see transaction rolled back")
def step_see_transaction_rolled_back(context):
    """
    Wait to see transaction rollback.
    """
    wrappers.expect_pager(context, "ROLLBACK\r\n", timeout=2)
