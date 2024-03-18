import platform
from setuptools import setup, find_packages

from pgcli import __version__

description = "CLI for Postgres Database. With auto-completion and syntax highlighting."

install_requirements = [
    "pgspecial>=2.0.0",
    "click >= 4.1",
    "Pygments>=2.0",  # Pygments has to be Capitalcased. WTF?
    # We still need to use pt-2 unless pt-3 released on Fedora32
    # see: https://github.com/dbcli/pgcli/pull/1197
    "prompt_toolkit>=2.0.6,<4.0.0",
    "psycopg >= 3.0.14; sys_platform != 'win32'",
    "psycopg-binary >= 3.0.14; sys_platform == 'win32'",
    "sqlparse >=0.3.0,<0.5",
    "configobj >= 5.0.6",
    "cli_helpers[styles] >= 2.2.1",
]


# setproctitle is used to mask the password when running `ps` in command line.
# But this is not necessary in Windows since the password is never shown in the
# task manager. Also setproctitle is a hard dependency to install in Windows,
# so we'll only install it if we're not in Windows.
if platform.system() != "Windows" and not platform.system().startswith("CYGWIN"):
    install_requirements.append("setproctitle >= 1.1.9")

setup(
    name="pgcli",
    author="Pgcli Core Team",
    author_email="pgcli-dev@googlegroups.com",
    version=__version__,
    license="BSD",
    url="http://pgcli.com",
    packages=find_packages(),
    package_data={"pgcli": ["pgclirc", "packages/pgliterals/pgliterals.json"]},
    description=description,
    long_description=open("README.rst").read(),
    install_requires=install_requirements,
    dependency_links=[
        "http://github.com/psycopg/repo/tarball/master#egg=psycopg-3.0.10"
    ],
    extras_require={
        "keyring": ["keyring >= 12.2.0"],
        "sshtunnel": ["sshtunnel >= 0.4.0"],
    },
    python_requires=">=3.8",
    entry_points="""
        [console_scripts]
        pgcli=pgcli.main:cli
    """,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: Unix",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: SQL",
        "Topic :: Database",
        "Topic :: Database :: Front-Ends",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
