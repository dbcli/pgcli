#!/usr/bin/env python
import re
import ast
import subprocess

def version():
    _version_re = re.compile(r'__version__\s+=\s+(.*)')

    with open('pgcli/__init__.py', 'rb') as f:
        version = str(ast.literal_eval(_version_re.search(
            f.read().decode('utf-8')).group(1)))

    return version

def create_git_tag(tag_name):
    cmd = ['git', 'tag', tag_name]
    print ' '.join(cmd)
    subprocess.check_output(cmd)

def register_with_pypi():
    cmd = ['python', 'setup.py', 'register']
    print ' '.join(cmd)
    subprocess.check_output(cmd)

def create_source_tarball():
    cmd = ['python', 'setup.py', 'sdist']
    print ' '.join(cmd)
    subprocess.check_output(cmd)

if __name__ == '__main__':
    ver = version()
    print ver
    create_git_tag('v%s' % ver)
    register_with_pypi()
    create_source_tarball()
