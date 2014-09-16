#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
        name='prompt_toolkit',
        author='Jonathan Slenders',
        version='0.11',
        license='LICENSE.txt',
        url='https://github.com/jonathanslenders/python-prompt-toolkit',

        description='Library for building powerful interactive command lines in Python',
        long_description='',
        packages=find_packages('.'),
        install_requires = [
            'pygments', 'docopt', 'six',

            # TODO: add wcwidth when released and stable on pypi
            # 'wcwidth',

            # Required for the Python repl
            'jedi',
        ],
        scripts = [
            'bin/ptpython',
            'bin/ptipython',
        ]
)
