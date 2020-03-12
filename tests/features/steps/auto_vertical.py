from textwrap import dedent
from behave import then, when
import wrappers


@when("we run dbcli with {arg}")
def step_run_cli_with_arg(context, arg):
    wrappers.run_cli(context, run_args=arg.split("="))


@when("we execute a small query")
def step_execute_small_query(context):
    context.cli.sendline("select 1")


@when("we execute a large query")
def step_execute_large_query(context):
    context.cli.sendline("select {}".format(",".join([str(n) for n in range(1, 50)])))


@then("we see small results in horizontal format")
def step_see_small_results(context):
    wrappers.expect_pager(
        context,
        dedent(
            """\
        +------------+\r
        | ?column?   |\r
        |------------|\r
        | 1          |\r
        +------------+\r
        SELECT 1\r
        """
        ),
        timeout=5,
    )


@then("we see large results in vertical format")
def step_see_large_results(context):
    wrappers.expect_pager(
        context,
        dedent(
            """\
        -[ RECORD 1 ]-------------------------\r
        ?column? | 1\r
        ?column? | 2\r
        ?column? | 3\r
        ?column? | 4\r
        ?column? | 5\r
        ?column? | 6\r
        ?column? | 7\r
        ?column? | 8\r
        ?column? | 9\r
        ?column? | 10\r
        ?column? | 11\r
        ?column? | 12\r
        ?column? | 13\r
        ?column? | 14\r
        ?column? | 15\r
        ?column? | 16\r
        ?column? | 17\r
        ?column? | 18\r
        ?column? | 19\r
        ?column? | 20\r
        ?column? | 21\r
        ?column? | 22\r
        ?column? | 23\r
        ?column? | 24\r
        ?column? | 25\r
        ?column? | 26\r
        ?column? | 27\r
        ?column? | 28\r
        ?column? | 29\r
        ?column? | 30\r
        ?column? | 31\r
        ?column? | 32\r
        ?column? | 33\r
        ?column? | 34\r
        ?column? | 35\r
        ?column? | 36\r
        ?column? | 37\r
        ?column? | 38\r
        ?column? | 39\r
        ?column? | 40\r
        ?column? | 41\r
        ?column? | 42\r
        ?column? | 43\r
        ?column? | 44\r
        ?column? | 45\r
        ?column? | 46\r
        ?column? | 47\r
        ?column? | 48\r
        ?column? | 49\r
        SELECT 1\r
        """
        ),
        timeout=5,
    )
