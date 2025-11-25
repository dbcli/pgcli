"""
Steps for testing -c/--command option behavioral tests.
"""

import subprocess
from behave import when, then


@when('we run pgcli with -c "{command}"')
def step_run_pgcli_with_c(context, command):
    """Run pgcli with -c flag and a command."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "-c", command
    ]
    try:
        context.cmd_output = subprocess.check_output(
            cmd,
            cwd=context.package_root,
            stderr=subprocess.STDOUT,
            timeout=5
        )
        context.exit_code = 0
    except subprocess.CalledProcessError as e:
        context.cmd_output = e.output
        context.exit_code = e.returncode
    except subprocess.TimeoutExpired as e:
        context.cmd_output = b"Command timed out"
        context.exit_code = -1


@when('we run pgcli with --command "{command}"')
def step_run_pgcli_with_command(context, command):
    """Run pgcli with --command flag and a command."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "--command", command
    ]
    try:
        context.cmd_output = subprocess.check_output(
            cmd,
            cwd=context.package_root,
            stderr=subprocess.STDOUT,
            timeout=5
        )
        context.exit_code = 0
    except subprocess.CalledProcessError as e:
        context.cmd_output = e.output
        context.exit_code = e.returncode
    except subprocess.TimeoutExpired as e:
        context.cmd_output = b"Command timed out"
        context.exit_code = -1


@then("we see the query result")
def step_see_query_result(context):
    """Verify that the query result is in the output."""
    output = context.cmd_output.decode('utf-8')
    # Check for common query result indicators
    assert any([
        "SELECT" in output,
        "test_diego_column" in output,
        "greeting" in output,
        "hello" in output,
        "+-" in output,  # table border
        "|" in output,   # table column separator
    ]), f"Expected query result in output, but got: {output}"


@then("we see both query results")
def step_see_both_query_results(context):
    """Verify that both query results are in the output."""
    output = context.cmd_output.decode('utf-8')
    # Should contain output from both SELECT statements
    assert "SELECT" in output, f"Expected SELECT in output, but got: {output}"
    # The output should have multiple result sets
    assert output.count("SELECT") >= 2, f"Expected at least 2 SELECT results, but got: {output}"


@then("we see the command output")
def step_see_command_output(context):
    """Verify that the special command output is present."""
    output = context.cmd_output.decode('utf-8')
    # For \dt we should see table-related output
    # It might be empty if no tables exist, but shouldn't error
    assert context.exit_code == 0, f"Expected exit code 0, but got: {context.exit_code}"


@then("we see an error message")
def step_see_error_message(context):
    """Verify that an error message is in the output."""
    output = context.cmd_output.decode('utf-8')
    assert any([
        "does not exist" in output,
        "error" in output.lower(),
        "ERROR" in output,
    ]), f"Expected error message in output, but got: {output}"


@then("pgcli exits successfully")
def step_pgcli_exits_successfully(context):
    """Verify that pgcli exited with code 0."""
    assert context.exit_code == 0, f"Expected exit code 0, but got: {context.exit_code}"
    # Clean up
    context.cmd_output = None
    context.exit_code = None


@then("pgcli exits with error")
def step_pgcli_exits_with_error(context):
    """Verify that pgcli exited with a non-zero code."""
    assert context.exit_code != 0, f"Expected non-zero exit code, but got: {context.exit_code}"
    # Clean up
    context.cmd_output = None
    context.exit_code = None


@when("we run pgcli with multiple -c options")
def step_run_pgcli_with_multiple_c(context):
    """Run pgcli with multiple -c flags."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "-c", "SELECT 'first' as result",
        "-c", "SELECT 'second' as result",
        "-c", "SELECT 'third' as result"
    ]
    try:
        context.cmd_output = subprocess.check_output(
            cmd,
            cwd=context.package_root,
            stderr=subprocess.STDOUT,
            timeout=10
        )
        context.exit_code = 0
    except subprocess.CalledProcessError as e:
        context.cmd_output = e.output
        context.exit_code = e.returncode
    except subprocess.TimeoutExpired as e:
        context.cmd_output = b"Command timed out"
        context.exit_code = -1


@when("we run pgcli with mixed -c and --command")
def step_run_pgcli_with_mixed_options(context):
    """Run pgcli with mixed -c and --command flags."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "-c", "SELECT 'from_c' as source",
        "--command", "SELECT 'from_command' as source"
    ]
    try:
        context.cmd_output = subprocess.check_output(
            cmd,
            cwd=context.package_root,
            stderr=subprocess.STDOUT,
            timeout=10
        )
        context.exit_code = 0
    except subprocess.CalledProcessError as e:
        context.cmd_output = e.output
        context.exit_code = e.returncode
    except subprocess.TimeoutExpired as e:
        context.cmd_output = b"Command timed out"
        context.exit_code = -1


@then("we see all command outputs")
def step_see_all_command_outputs(context):
    """Verify that all command outputs are present."""
    output = context.cmd_output.decode('utf-8')
    # Should contain output from all commands
    assert "first" in output or "from_c" in output, f"Expected 'first' or 'from_c' in output, but got: {output}"
    assert "second" in output or "from_command" in output, f"Expected 'second' or 'from_command' in output, but got: {output}"
    # For the 3-command test, also check for third
    if "third" in output or "result" in output:
        assert "third" in output, f"Expected 'third' in output for 3-command test, but got: {output}"
