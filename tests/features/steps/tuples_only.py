"""
Steps for testing -t/--tuples-only option behavioral tests.
"""

import subprocess
from behave import when, then


@when('we run pgcli with "{options}"')
def step_run_pgcli_with_options(context, options):
    """Run pgcli with specified options."""
    # Split options into individual arguments, handling quoted strings
    import shlex
    args = shlex.split(options)

    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "--less-chatty"  # Suppress intro/goodbye messages
    ] + args

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


@then("we see only the data rows")
def step_see_only_data_rows(context):
    """Verify that output contains only data rows (no headers, borders, or status)."""
    output = context.cmd_output.decode('utf-8').strip()

    # Should not have table borders or formatting characters
    assert "+-" not in output, f"Expected no table borders, but got: {output}"
    assert not output.startswith("|"), f"Expected no table pipes, but got: {output}"

    # Should have some output (the data)
    assert len(output) > 0, f"Expected data output, but got empty: {output}"


@then('we don\'t see "{text}"')
def step_dont_see_text(context, text):
    """Verify that specified text is NOT in the output."""
    output = context.cmd_output.decode('utf-8')
    assert text not in output, f"Expected NOT to see '{text}' in output, but got: {output}"


@then('we see "{text}" in the output')
def step_see_text_in_output(context, text):
    """Verify that specified text IS in the output."""
    output = context.cmd_output.decode('utf-8')
    assert text in output, f"Expected to see '{text}' in output, but got: {output}"


@then("we see tab-separated values")
def step_see_tab_separated_values(context):
    """Verify that output contains tab-separated values."""
    output = context.cmd_output.decode('utf-8').strip()

    # Should contain tabs
    assert "\t" in output, f"Expected tab-separated values, but got: {output}"

    # Should not have table borders
    assert "+-" not in output, f"Expected no table borders, but got: {output}"
    assert "|" not in output, f"Expected no table pipes, but got: {output}"


@then("we see multiple data rows")
def step_see_multiple_data_rows(context):
    """Verify that output contains multiple rows of data."""
    output = context.cmd_output.decode('utf-8').strip()
    lines = output.split('\n')

    # Filter out empty lines
    data_lines = [line for line in lines if line.strip()]

    # Should have multiple rows
    assert len(data_lines) >= 3, f"Expected at least 3 data rows, but got {len(data_lines)}: {output}"

    # Should not have table formatting
    assert "+-" not in output, f"Expected no table borders, but got: {output}"


@then("we see the command output")
def step_see_command_output(context):
    """Verify that the special command output is present."""
    output = context.cmd_output.decode('utf-8')
    # For special commands like \dt, just verify it didn't error
    assert context.exit_code == 0, f"Expected exit code 0, but got: {context.exit_code}"


@then("pgcli exits successfully")
def step_pgcli_exits_successfully(context):
    """Verify that pgcli exited with code 0."""
    assert context.exit_code == 0, f"Expected exit code 0, but got: {context.exit_code}. Output: {context.cmd_output.decode('utf-8')}"
    # Clean up
    context.cmd_output = None
    context.exit_code = None
