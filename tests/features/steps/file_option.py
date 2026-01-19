"""
Steps for testing -f/--file option behavioral tests.
"""

import subprocess
import tempfile
import os
from behave import when, then


@when('we create a file with "{content}"')
def step_create_file_with_content(context, content):
    """Create a temporary file with the given content."""
    # Create a temporary file that will be cleaned up automatically
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        delete=False,
        suffix='.sql'
    )
    temp_file.write(content)
    temp_file.close()
    context.temp_file_path = temp_file.name


@when('we run pgcli with -f and the file')
def step_run_pgcli_with_f(context):
    """Run pgcli with -f flag and the temporary file."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "-f", context.temp_file_path
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
    finally:
        # Clean up the temporary file
        if hasattr(context, 'temp_file_path') and os.path.exists(context.temp_file_path):
            os.unlink(context.temp_file_path)


@when('we run pgcli with --file and the file')
def step_run_pgcli_with_file(context):
    """Run pgcli with --file flag and the temporary file."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "--file", context.temp_file_path
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
    finally:
        # Clean up the temporary file
        if hasattr(context, 'temp_file_path') and os.path.exists(context.temp_file_path):
            os.unlink(context.temp_file_path)


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
