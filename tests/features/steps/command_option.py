"""Steps for the -c/--command option.

The steps shared with the -f/--file scenarios (query result, command output,
error message, exit status) are defined once in file_option.py; behave's step
registry is global, so redefining them here would raise AmbiguousStep.
"""

import subprocess
from behave import when, then


@when('we run pgcli with -c "{command}"')
def step_run_pgcli_with_c(context, command):
    """Run pgcli with -c flag and a command."""
    cmd = [
        "pgcli",
        "-h",
        context.conf["host"],
        "-p",
        str(context.conf["port"]),
        "-U",
        context.conf["user"],
        "-d",
        context.conf["dbname"],
        "-c",
        command,
    ]
    try:
        context.cmd_output = subprocess.check_output(cmd, cwd=context.package_root, stderr=subprocess.STDOUT, timeout=5)
        context.exit_code = 0
    except subprocess.CalledProcessError as e:
        context.cmd_output = e.output
        context.exit_code = e.returncode
    except subprocess.TimeoutExpired:
        context.cmd_output = b"Command timed out"
        context.exit_code = -1


@when('we run pgcli with --command "{command}"')
def step_run_pgcli_with_command(context, command):
    """Run pgcli with --command flag and a command."""
    cmd = [
        "pgcli",
        "-h",
        context.conf["host"],
        "-p",
        str(context.conf["port"]),
        "-U",
        context.conf["user"],
        "-d",
        context.conf["dbname"],
        "--command",
        command,
    ]
    try:
        context.cmd_output = subprocess.check_output(cmd, cwd=context.package_root, stderr=subprocess.STDOUT, timeout=5)
        context.exit_code = 0
    except subprocess.CalledProcessError as e:
        context.cmd_output = e.output
        context.exit_code = e.returncode
    except subprocess.TimeoutExpired:
        context.cmd_output = b"Command timed out"
        context.exit_code = -1


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
        "-h",
        context.conf["host"],
        "-p",
        str(context.conf["port"]),
        "-U",
        context.conf["user"],
        "-d",
        context.conf["dbname"],
        "-c",
        "SELECT 'first' as result",
        "-c",
        "SELECT 'second' as result",
        "-c",
        "SELECT 'third' as result",
    ]
    try:
        context.cmd_output = subprocess.check_output(cmd, cwd=context.package_root, stderr=subprocess.STDOUT, timeout=10)
        context.exit_code = 0
    except subprocess.CalledProcessError as e:
        context.cmd_output = e.output
        context.exit_code = e.returncode
    except subprocess.TimeoutExpired:
        context.cmd_output = b"Command timed out"
        context.exit_code = -1


@when("we run pgcli with mixed -c and --command")
def step_run_pgcli_with_mixed_options(context):
    """Run pgcli with mixed -c and --command flags."""
    cmd = [
        "pgcli",
        "-h",
        context.conf["host"],
        "-p",
        str(context.conf["port"]),
        "-U",
        context.conf["user"],
        "-d",
        context.conf["dbname"],
        "-c",
        "SELECT 'from_c' as source",
        "--command",
        "SELECT 'from_command' as source",
    ]
    try:
        context.cmd_output = subprocess.check_output(cmd, cwd=context.package_root, stderr=subprocess.STDOUT, timeout=10)
        context.exit_code = 0
    except subprocess.CalledProcessError as e:
        context.cmd_output = e.output
        context.exit_code = e.returncode
    except subprocess.TimeoutExpired:
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
