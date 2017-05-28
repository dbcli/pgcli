#!/usr/bin/env python
from __future__ import print_function
import re
import ast
import subprocess
import sys
from optparse import OptionParser

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
        choice = raw_input("--- Confirm step? (y/N) [y] ")
        if choice.lower() == 'n':
            return True
    return False


def run_step(*args):
    """
    Prints out the command and asks if it should be run.
    If yes (default), runs it.
    :param args: list of strings (command and args)
    """
    global DRY_RUN

    cmd = args
    print(' '.join(cmd))
    if skip_step():
        print('--- Skipping...')
    elif DRY_RUN:
        print('--- Pretending to run...')
    else:
        subprocess.check_output(cmd)


def version(version_file):
    _version_re = re.compile(r'__version__\s+=\s+(.*)')

    with open(version_file, 'rb') as f:
        ver = str(ast.literal_eval(_version_re.search(
            f.read().decode('utf-8')).group(1)))

    return ver


def commit_for_release(version_file, ver):
    run_step('git', 'reset')
    run_step('git', 'add', version_file)
    run_step('git', 'commit', '--message', 'Releasing version %s' % ver)


def create_git_tag(tag_name):
    run_step('git', 'tag', tag_name)


def create_source_tarball():
    run_step('python', 'setup.py', 'sdist')


def upload_source_tarball():
    run_step('python', 'setup.py', 'sdist', 'upload')


def push_to_github():
    run_step('git', 'push', 'origin', 'master')


def push_tags_to_github():
    run_step('git', 'push', '--tags', 'origin')


if __name__ == '__main__':
    if DEBUG:
        subprocess.check_output = lambda x: x

    ver = version('pgcli/__init__.py')
    print('Releasing Version:', ver)

    parser = OptionParser()
    parser.add_option(
        "-c", "--confirm-steps", action="store_true", dest="confirm_steps",
        default=False, help=("Confirm every step. If the step is not "
                             "confirmed, it will be skipped.")
    )
    parser.add_option(
        "-d", "--dry-run", action="store_true", dest="dry_run",
        default=False, help="Print out, but not actually run any steps."
    )

    popts, pargs = parser.parse_args()
    CONFIRM_STEPS = popts.confirm_steps
    DRY_RUN = popts.dry_run

    choice = raw_input('Are you sure? (y/N) [n] ')
    if choice.lower() != 'y':
        sys.exit(1)

    commit_for_release('pgcli/__init__.py', ver)
    create_git_tag('v%s' % ver)
    create_source_tarball()
    push_to_github()
    push_tags_to_github()
    upload_source_tarball()
