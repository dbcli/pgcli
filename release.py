#!/usr/bin/env python
"""A script to publish a release of pgcli to PyPI."""

import io
from optparse import OptionParser
import re
import subprocess
import sys

import click

DEBUG = False
CONFIRM_STEPS = False
DRY_RUN = False


def skip_step():
    """
    Asks for user's response whether to run a step. Default is yes.
    :return: boolean
    """
    global CONFIRM_STEPS

    if CONFIRM_STEPS:
        return not click.confirm("--- Run this step?", default=True)
    return False


def run_step(*args):
    """
    Prints out the command and asks if it should be run.
    If yes (default), runs it.
    :param args: list of strings (command and args)
    """
    global DRY_RUN

    cmd = args
    print(" ".join(cmd))
    if skip_step():
        print("--- Skipping...")
    elif DRY_RUN:
        print("--- Pretending to run...")
    else:
        subprocess.check_output(cmd)


def version(version_file):
    _version_re = re.compile(
        r'__version__\s+=\s+(?P<quote>[\'"])(?P<version>.*)(?P=quote)'
    )

    with io.open(version_file, encoding="utf-8") as f:
        ver = _version_re.search(f.read()).group("version")

    return ver


def commit_for_release(version_file, ver):
    run_step("git", "reset")
    run_step("git", "add", version_file)
    run_step("git", "commit", "--message", "Releasing version {}".format(ver))


def create_git_tag(tag_name):
    run_step("git", "tag", tag_name)


def create_distribution_files():
    run_step("python", "setup.py", "clean", "--all", "sdist", "bdist_wheel")


def upload_distribution_files():
    run_step("twine", "upload", "dist/*")


def push_to_github():
    run_step("git", "push", "origin", "master")


def push_tags_to_github():
    run_step("git", "push", "--tags", "origin")


def checklist(questions):
    for question in questions:
        if not click.confirm("--- {}".format(question), default=False):
            sys.exit(1)


if __name__ == "__main__":
    if DEBUG:
        subprocess.check_output = lambda x: x

    checks = [
        "Have you updated the AUTHORS file?",
        "Have you updated the `Usage` section of the README?",
    ]
    checklist(checks)

    ver = version("pgcli/__init__.py")
    print("Releasing Version:", ver)

    parser = OptionParser()
    parser.add_option(
        "-c",
        "--confirm-steps",
        action="store_true",
        dest="confirm_steps",
        default=False,
        help=(
            "Confirm every step. If the step is not " "confirmed, it will be skipped."
        ),
    )
    parser.add_option(
        "-d",
        "--dry-run",
        action="store_true",
        dest="dry_run",
        default=False,
        help="Print out, but not actually run any steps.",
    )

    popts, pargs = parser.parse_args()
    CONFIRM_STEPS = popts.confirm_steps
    DRY_RUN = popts.dry_run

    if not click.confirm("Are you sure?", default=False):
        sys.exit(1)

    commit_for_release("pgcli/__init__.py", ver)
    create_git_tag("v{}".format(ver))
    create_distribution_files()
    push_to_github()
    push_tags_to_github()
    upload_distribution_files()
