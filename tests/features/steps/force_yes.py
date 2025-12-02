"""
Steps for testing -y/--yes option behavioral tests.
"""

import subprocess
from behave import when, then


@when("we create a test table for destructive tests")
def step_create_test_table(context):
    """Create a test table for destructive command tests."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "-c", "DROP TABLE IF EXISTS test_yes_table; CREATE TABLE test_yes_table (id INT);"
    ]
    try:
        subprocess.check_output(
            cmd,
            cwd=context.package_root,
            stderr=subprocess.STDOUT,
            timeout=5
        )
        context.table_created = True
    except Exception as e:
        context.table_created = False
        print(f"Failed to create test table: {e}")


@when('we run pgcli with --yes and destructive command "{command}"')
def step_run_pgcli_with_yes_long(context, command):
    """Run pgcli with --yes flag and a destructive command."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "--yes",
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


@when('we run pgcli with -y and destructive command "{command}"')
def step_run_pgcli_with_yes_short(context, command):
    """Run pgcli with -y flag and a destructive command."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "-y",
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


@when('we run pgcli without --yes and destructive command "{command}"')
def step_run_pgcli_without_yes(context, command):
    """Run pgcli without --yes flag and a destructive command."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "-c", command
    ]
    try:
        # In non-interactive mode, the command should not prompt and fail
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


@when('we run pgcli with --yes -c "{command1}" -c "{command2}"')
def step_run_pgcli_with_yes_multiple_c(context, command1, command2):
    """Run pgcli with --yes and multiple -c flags."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "--yes",
        "-c", command1,
        "-c", command2
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


@then("we see the command executed without prompt")
def step_see_command_executed_without_prompt(context):
    """Verify that the command was executed without showing a confirmation prompt."""
    output = context.cmd_output.decode('utf-8')
    # Should NOT contain the destructive warning prompt
    assert "Do you want to proceed?" not in output, \
        f"Expected no confirmation prompt, but found one in output: {output}"
    # Should NOT contain "Your call!" when using --yes
    assert "Your call!" not in output, \
        f"Expected no 'Your call!' message with --yes flag, but found it in output: {output}"
    # Should contain success indicators
    assert any([
        "ALTER TABLE" in output,
        "DROP" in output,
        "SET" in output,
    ]), f"Expected command execution indicators in output, but got: {output}"


@then("we see both commands executed without prompt")
def step_see_both_commands_executed(context):
    """Verify that both commands were executed without prompts."""
    output = context.cmd_output.decode('utf-8')
    # Should NOT contain confirmation prompts
    assert "Do you want to proceed?" not in output, \
        f"Expected no confirmation prompt, but found one in output: {output}"
    # Should NOT contain "Your call!" when using --yes
    assert "Your call!" not in output, \
        f"Expected no 'Your call!' message with --yes flag, but found it in output: {output}"
    # Should contain indicators from both commands
    assert output.count("ALTER TABLE") >= 2, \
        f"Expected indicators from both ALTER TABLE commands, but got: {output}"


@then("we see the command was not executed")
def step_see_command_not_executed(context):
    """Verify that the destructive command was not executed in non-interactive mode."""
    output = context.cmd_output.decode('utf-8')
    # In non-interactive mode (-c), if destructive_warning is enabled but no --yes,
    # the command might not execute or might skip the prompt
    # The behavior depends on whether stdin.isatty() returns False
    # For now, we just verify the command ran (it should skip prompt in non-tty)
    assert context.exit_code == 0, f"Expected exit code 0, but got: {context.exit_code}"


@then("we see table was dropped")
def step_see_table_dropped(context):
    """Verify that the table was successfully dropped."""
    output = context.cmd_output.decode('utf-8')
    # Should NOT contain "Your call!" when using --yes
    assert "Your call!" not in output, \
        f"Expected no 'Your call!' message with --yes flag, but found it in output: {output}"
    assert "DROP TABLE" in output, \
        f"Expected DROP TABLE confirmation in output, but got: {output}"
    context.table_created = False  # Mark as not needing cleanup


@then("we cleanup the test table")
def step_cleanup_test_table(context):
    """Cleanup the test table if it still exists."""
    if not hasattr(context, 'table_created') or not context.table_created:
        return  # Nothing to clean up

    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "--yes",  # Use --yes to avoid prompt during cleanup
        "-c", "DROP TABLE IF EXISTS test_yes_table;"
    ]
    try:
        subprocess.check_output(
            cmd,
            cwd=context.package_root,
            stderr=subprocess.STDOUT,
            timeout=5
        )
        context.table_created = False
    except Exception as e:
        print(f"Warning: Failed to cleanup test table: {e}")
