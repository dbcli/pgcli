import copy
import os
import shutil
import signal
import sys
import tempfile

import db_utils as dbutils
import fixture_utils as fixutils
import pexpect

from steps import wrappers


def before_all(context):
    """Set env parameters."""
    env_old = copy.deepcopy(dict(os.environ))
    os.environ["LINES"] = "100"
    os.environ["COLUMNS"] = "100"
    os.environ["PAGER"] = "cat"
    os.environ["EDITOR"] = "ex"
    os.environ["VISUAL"] = "ex"
    os.environ["PROMPT_TOOLKIT_NO_CPR"] = "1"

    context.package_root = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    fixture_dir = os.path.join(context.package_root, "tests/features/fixture_data")

    print("package root:", context.package_root)
    print("fixture dir:", fixture_dir)

    os.environ["COVERAGE_PROCESS_START"] = os.path.join(context.package_root, ".coveragerc")

    context.exit_sent = False

    vi = "_".join([str(x) for x in sys.version_info[:3]])
    db_name = context.config.userdata.get("pg_test_db", "pgcli_behave_tests")
    db_name_full = f"{db_name}_{vi}"

    # Store get params from config.
    context.conf = {
        "host": context.config.userdata.get("pg_test_host", os.getenv("PGHOST", "localhost")),
        "user": context.config.userdata.get("pg_test_user", os.getenv("PGUSER", "postgres")),
        "pass": context.config.userdata.get("pg_test_pass", os.getenv("PGPASSWORD", None)),
        "port": context.config.userdata.get("pg_test_port", os.getenv("PGPORT", "5432")),
        "cli_command": (
            context.config.userdata.get("pg_cli_command", None)
            or '{python} -c "{startup}"'.format(
                python=sys.executable,
                startup="; ".join([
                    "import coverage",
                    "coverage.process_startup()",
                    "import pgcli.main",
                    "pgcli.main.cli(auto_envvar_prefix='BEHAVE')",
                ]),
            )
        ),
        "dbname": db_name_full,
        "dbname_tmp": db_name_full + "_tmp",
        "vi": vi,
        "pager_boundary": "---boundary---",
    }
    os.environ["PAGER"] = "{0} {1} {2}".format(
        sys.executable,
        os.path.join(context.package_root, "tests/features/wrappager.py"),
        context.conf["pager_boundary"],
    )

    # Store old env vars.
    context.pgenv = {
        "PGDATABASE": os.environ.get("PGDATABASE", None),
        "PGUSER": os.environ.get("PGUSER", None),
        "PGHOST": os.environ.get("PGHOST", None),
        "PGPASSWORD": os.environ.get("PGPASSWORD", None),
        "PGPORT": os.environ.get("PGPORT", None),
        "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME", None),
        "PGSERVICEFILE": os.environ.get("PGSERVICEFILE", None),
    }

    # Set new env vars.
    os.environ["PGDATABASE"] = context.conf["dbname"]
    os.environ["PGUSER"] = context.conf["user"]
    os.environ["PGHOST"] = context.conf["host"]
    os.environ["PGPORT"] = context.conf["port"]
    os.environ["PGSERVICEFILE"] = os.path.join(fixture_dir, "mock_pg_service.conf")

    if context.conf["pass"]:
        os.environ["PGPASSWORD"] = context.conf["pass"]
    else:
        if "PGPASSWORD" in os.environ:
            del os.environ["PGPASSWORD"]
    os.environ["BEHAVE_WARN"] = "moderate"

    context.cn = dbutils.create_db(
        context.conf["host"],
        context.conf["user"],
        context.conf["pass"],
        context.conf["dbname"],
        context.conf["port"],
    )
    context.pgbouncer_available = dbutils.pgbouncer_available(
        hostname=context.conf["host"],
        password=context.conf["pass"],
        username=context.conf["user"],
    )
    context.fixture_data = fixutils.read_fixture_files()

    # use temporary directory as config home
    context.env_config_home = tempfile.mkdtemp(prefix="pgcli_home_")
    os.environ["XDG_CONFIG_HOME"] = context.env_config_home
    show_env_changes(env_old, dict(os.environ))


def show_env_changes(env_old, env_new):
    """Print out all test-specific env values."""
    print("--- os.environ changed values: ---")
    all_keys = env_old.keys() | env_new.keys()
    for k in sorted(all_keys):
        old_value = env_old.get(k, "")
        new_value = env_new.get(k, "")
        if new_value and old_value != new_value:
            print(f'{k}="{new_value}"')
    print("-" * 20)


def after_all(context):
    """
    Unset env parameters.
    """
    dbutils.close_cn(context.cn)
    dbutils.drop_db(
        context.conf["host"],
        context.conf["user"],
        context.conf["pass"],
        context.conf["dbname"],
        context.conf["port"],
    )

    # Remove temp config directory
    shutil.rmtree(context.env_config_home)

    # Restore env vars.
    for k, v in context.pgenv.items():
        if k in os.environ and v is None:
            del os.environ[k]
        elif v:
            os.environ[k] = v


def before_step(context, _):
    context.atprompt = False


def is_known_problem(scenario):
    """TODO: can we fix this?"""
    return scenario.name in (
        'interrupt current query via "ctrl + c"',
        "run the cli with --username",
        "run the cli with --user",
        "run the cli with --port",
        "confirm exit when a transaction is ongoing",
        "cancel exit when a transaction is ongoing",
        "run the cli and exit",
    )


def before_scenario(context, scenario):
    if scenario.name == "list databases":
        # not using the cli for that
        return
    if is_known_problem(scenario):
        scenario.skip()
    currentdb = None
    if "pgbouncer" in scenario.feature.tags:
        if context.pgbouncer_available:
            os.environ["PGDATABASE"] = "pgbouncer"
            os.environ["PGPORT"] = "6432"
            currentdb = "pgbouncer"
        else:
            scenario.skip()
    else:
        # set env vars back to normal test database
        os.environ["PGDATABASE"] = context.conf["dbname"]
        os.environ["PGPORT"] = context.conf["port"]
    wrappers.run_cli(context, currentdb=currentdb)
    wrappers.wait_prompt(context)


def after_scenario(context, scenario):
    """Cleans up after each scenario completes."""
    if hasattr(context, "cli") and context.cli and not context.exit_sent:
        # Quit nicely.
        if not getattr(context, "atprompt", False):
            dbname = context.currentdb
            context.cli.expect_exact(f"{dbname}>", timeout=5)
        try:
            context.cli.sendcontrol("c")
            context.cli.sendcontrol("d")
        except Exception as x:
            print("Failed cleanup after scenario:")
            print(x)
        try:
            context.cli.expect_exact(pexpect.EOF, timeout=5)
        except pexpect.TIMEOUT:
            print(f"--- after_scenario {scenario.name}: kill cli")
            context.cli.kill(signal.SIGKILL)
    if hasattr(context, "tmpfile_sql_help") and context.tmpfile_sql_help:
        context.tmpfile_sql_help.close()
        context.tmpfile_sql_help = None


# # TODO: uncomment to debug a failure
# def after_step(context, step):
#     if step.status == "failed":
#         import pdb; pdb.set_trace()
