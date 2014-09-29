#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
        name='prompt_toolkit',
        author='Jonathan Slenders',
        version='0.16',
        license='LICENSE.txt',
        url='https://github.com/jonathanslenders/python-prompt-toolkit',

        description='Library for building powerful interactive command lines in Python',
        long_description='',
        packages=find_packages('.'),
        install_requires = [
            'docopt',
            'jedi',
            'pygments',
            'six',
            'wcwidth',
        ],
        scripts = [
            'bin/ptpython',
            'bin/ptipython',
        ]
)
