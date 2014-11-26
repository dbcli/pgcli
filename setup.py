import re
import ast
from setuptools import setup, find_packages

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('pgcli/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
        name='pgcli',
        author='Amjith Ramanujam',
        version=version,
        license='LICENSE.txt',
        url='https://github.com/amjith/pgcli',
        packages=find_packages(),
        description='CLI for Postgres. With auto-completion and '
                    'syntax highlighting',
        install_requires=[
            'Click',
            'prompt_toolkit',
            'psycopg2',
            'tabulate',
            'sqlparse',
            ],
        entry_points='''
            [console_scripts]
            pgcli=pgcli.main:cli
        ''',
        classifiers=[
            'License :: OSI Approved :: BSD License',
            'Programming Language :: Python',
            'Programming Language :: Python :: 3'
            ],
        )
