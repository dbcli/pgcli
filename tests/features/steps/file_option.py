"""
Steps for testing -f/--file option behavioral tests.
Reuses common steps from command_option.py
"""

import subprocess
import tempfile
import os
from behave import when


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


@when('we run pgcli with -c "{command}" and -f with the file')
def step_run_pgcli_with_c_and_f(context, command):
    """Run pgcli with both -c and -f flags."""
    cmd = [
        "pgcli",
        "-h", context.conf["host"],
        "-p", str(context.conf["port"]),
        "-U", context.conf["user"],
        "-d", context.conf["dbname"],
        "-c", command,
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
