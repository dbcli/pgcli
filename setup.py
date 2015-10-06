#!/usr/bin/env python
import os
from setuptools import setup, find_packages


long_description = open(
    os.path.join(
        os.path.dirname(__file__),
        'README.rst'
    )
).read()


setup(
    name='prompt_toolkit',
    author='Jonathan Slenders',
    version='0.53',
    license='LICENSE.txt',
    url='https://github.com/jonathanslenders/python-prompt-toolkit',
    description='Library for building powerful interactive command lines in Python',
    long_description=long_description,
    packages=find_packages('.'),
    install_requires = [
        'pygments',
        'six>=1.9.0',
        'wcwidth',
    ],
)
