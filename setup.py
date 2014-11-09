#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
        name='prompt_toolkit',
        author='Jonathan Slenders',
        version='0.22',
        license='LICENSE.txt',
        url='https://github.com/jonathanslenders/python-prompt-toolkit',

        description='Library for building powerful interactive command lines in Python',
        long_description='',
        packages=find_packages('.'),
        install_requires = [
            'docopt',
            'jedi>=0.8.1',
            'pygments',
            'six>=1.8.0',
            'wcwidth',
        ],
        entry_points={
            'console_scripts': [
                'ptpython = prompt_toolkit.contrib.entry_points.ptpython:run',
                'ptipython = prompt_toolkit.contrib.entry_points.ptipython:run',
            ]
        },
        extras_require = {
            'ptipython':  ['ipython'] # For ptipython, we need to have IPython
        }
)
