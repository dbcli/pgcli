A REPL for Postgres
-------------------

|Build Status| |CodeCov| |PyPI| |Landscape| |Gitter|

This is a postgres client that does auto-completion and syntax highlighting.

Home Page: http://pgcli.com

MySQL Equivalent: http://mycli.net

.. image:: screenshots/pgcli.gif
.. image:: screenshots/image01.png

Quick Start
-----------

If you already know how to install python packages, then you can simply do:

::

    $ pip install -U pgcli

    or

    $ sudo apt-get install pgcli # Only on Debian based Linux (e.g. Ubuntu, Mint, etc)
    $ brew install pgcli  # Only on macOS

If you don't know how to install python packages, please check the
`detailed instructions`_.

If you are restricted to using psycopg2 2.7.x then pip will try to install it from a binary. There are some known issues with the psycopg2 2.7 binary - see the `psycopg docs`_ for more information about this and how to force installation from source. psycopg2 2.8 has fixed these problems, and will build from source.

.. _`detailed instructions`: https://github.com/dbcli/pgcli#detailed-installation-instructions
.. _`psycopg docs`: http://initd.org/psycopg/docs/install.html#change-in-binary-packages-between-psycopg-2-7-and-2-8

Usage
-----

::

    $ pgcli [database_name]

    or

    $ pgcli postgresql://[user[:password]@][netloc][:port][/dbname][?extra=value[&other=other-value]]

Examples:

::

    $ pgcli local_database

    $ pgcli postgres://amjith:pa$$w0rd@example.com:5432/app_db?sslmode=verify-ca&sslrootcert=/myrootcert

For more details:

::

    $ pgcli --help

    Usage: pgcli [OPTIONS] [DBNAME] [USERNAME]

    Options:
      -h, --host TEXT         Host address of the postgres database.
      -p, --port INTEGER      Port number at which the postgres instance is
                              listening.
      -U, --username TEXT     Username to connect to the postgres database.
      -u, --user TEXT         Username to connect to the postgres database.
      -W, --password          Force password prompt.
      -w, --no-password       Never prompt for password.
      --single-connection     Do not use a separate connection for completions.
      -v, --version           Version of pgcli.
      -d, --dbname TEXT       database name to connect to.
      --pgclirc PATH          Location of pgclirc file.
      -D, --dsn TEXT          Use DSN configured into the [alias_dsn] section of
                              pgclirc file.
      --list-dsn              list of DSN configured into the [alias_dsn] section
                              of pgclirc file.
      --row-limit INTEGER     Set threshold for row limit prompt. Use 0 to disable
                              prompt.
      --less-chatty           Skip intro on startup and goodbye on exit.
      --prompt TEXT           Prompt format (Default: "\u@\h:\d> ").
      --prompt-dsn TEXT       Prompt format for connections using DSN aliases
                              (Default: "\u@\h:\d> ").
      -l, --list              list available databases, then exit.
      --auto-vertical-output  Automatically switch to vertical output mode if the
                              result is wider than the terminal width.
      --warn / --no-warn      Warn before running a destructive query.
      --help                  Show this message and exit.

``pgcli`` also supports many of the same `environment variables`_ as ``psql`` for login options (e.g. ``PGHOST``, ``PGPORT``, ``PGUSER``, ``PGPASSWORD``, ``PGDATABASE``).

The SSL-related environment variables are also supported, so if you need to connect a postgres database via ssl connection, you can set set environment like this:

::

    export PGSSLMODE="verify-full"
    export PGSSLCERT="/your-path-to-certs/client.crt"
    export PGSSLKEY="/your-path-to-keys/client.key"
    export PGSSLROOTCERT="/your-path-to-ca/ca.crt"
    pgcli -h localhost -p 5432 -U username postgres

.. _environment variables: https://www.postgresql.org/docs/current/libpq-envars.html

Features
--------

The `pgcli` is written using prompt_toolkit_.

* Auto-completes as you type for SQL keywords as well as tables and
  columns in the database.
* Syntax highlighting using Pygments.
* Smart-completion (enabled by default) will suggest context-sensitive
  completion.

    - ``SELECT * FROM <tab>`` will only show table names.
    - ``SELECT * FROM users WHERE <tab>`` will only show column names.

* Primitive support for ``psql`` back-slash commands.
* Pretty prints tabular data.

.. _prompt_toolkit: https://github.com/jonathanslenders/python-prompt-toolkit
.. _tabulate: https://pypi.python.org/pypi/tabulate

Config
------
A config file is automatically created at ``~/.config/pgcli/config`` at first launch.
See the file itself for a description of all available options.

Contributions:
--------------

If you're interested in contributing to this project, first of all I would like
to extend my heartfelt gratitude. I've written a small doc to describe how to
get this running in a development setup.

https://github.com/dbcli/pgcli/blob/master/DEVELOP.rst

Please feel free to reach out to me if you need help.
My email: amjith.r@gmail.com, Twitter: `@amjithr <http://twitter.com/amjithr>`_

Detailed Installation Instructions:
-----------------------------------

macOS:
======

The easiest way to install pgcli is using Homebrew.

::

    $ brew install pgcli

Done!

Alternatively, you can install ``pgcli`` as a python package using a package
manager called called ``pip``. You will need postgres installed on your system
for this to work.

In depth getting started guide for ``pip`` - https://pip.pypa.io/en/latest/installing.html.

::

    $ which pip

If it is installed then you can do:

::

    $ pip install pgcli

If that fails due to permission issues, you might need to run the command with
sudo permissions.

::

    $ sudo pip install pgcli

If pip is not installed check if easy_install is available on the system.

::

    $ which easy_install

    $ sudo easy_install pgcli

Linux:
======

In depth getting started guide for ``pip`` - https://pip.pypa.io/en/latest/installing.html.

Check if pip is already available in your system.

::

    $ which pip

If it doesn't exist, use your linux package manager to install `pip`. This
might look something like:

::

    $ sudo apt-get install python-pip   # Debian, Ubuntu, Mint etc

    or

    $ sudo yum install python-pip  # RHEL, Centos, Fedora etc

``pgcli`` requires python-dev, libpq-dev and libevent-dev packages. You can
install these via your operating system package manager.


::

    $ sudo apt-get install python-dev libpq-dev libevent-dev

    or

    $ sudo yum install python-devel postgresql-devel

Then you can install pgcli:

::

    $ sudo pip install pgcli


Docker
======

Pgcli can be run from within Docker. This can be useful to try pgcli without
installing it, or any dependencies, system-wide.

To build the image:

::

    $ docker build -t pgcli .

To create a container from the image:

::

    $ docker run --rm -ti pgcli pgcli <ARGS>

To access postgresql databases listening on localhost, make sure to run the
docker in "host net mode". E.g. to access a database called "foo" on the
postgresql server running on localhost:5432 (the standard port):

::

    $ docker run --rm -ti --net host pgcli pgcli -h localhost foo

To connect to a locally running instance over a unix socket, bind the socket to
the docker container:

::

    $ docker run --rm -ti -v /var/run/postgres:/var/run/postgres pgcli pgcli foo


IPython
=======

Pgcli can be run from within `IPython <https://ipython.org>`_ console. When working on a query,
it may be useful to drop into a pgcli session without leaving the IPython console, iterate on a
query, then quit pgcli to find the query results in your IPython workspace.

Assuming you have IPython installed:

::

    $ pip install ipython-sql

After that, run ipython and load the ``pgcli.magic`` extension:

::

    $ ipython

    In [1]: %load_ext pgcli.magic


Connect to a database and construct a query:

::

    In [2]: %pgcli postgres://someone@localhost:5432/world
    Connected: someone@world
    someone@localhost:world> select * from city c where countrycode = 'USA' and population > 1000000;
    +------+--------------+---------------+--------------+--------------+
    | id   | name         | countrycode   | district     | population   |
    |------+--------------+---------------+--------------+--------------|
    | 3793 | New York     | USA           | New York     | 8008278      |
    | 3794 | Los Angeles  | USA           | California   | 3694820      |
    | 3795 | Chicago      | USA           | Illinois     | 2896016      |
    | 3796 | Houston      | USA           | Texas        | 1953631      |
    | 3797 | Philadelphia | USA           | Pennsylvania | 1517550      |
    | 3798 | Phoenix      | USA           | Arizona      | 1321045      |
    | 3799 | San Diego    | USA           | California   | 1223400      |
    | 3800 | Dallas       | USA           | Texas        | 1188580      |
    | 3801 | San Antonio  | USA           | Texas        | 1144646      |
    +------+--------------+---------------+--------------+--------------+
    SELECT 9
    Time: 0.003s


Exit out of pgcli session with ``Ctrl + D`` and find the query results:

::

    someone@localhost:world>
    Goodbye!
    9 rows affected.
    Out[2]:
    [(3793, u'New York', u'USA', u'New York', 8008278),
     (3794, u'Los Angeles', u'USA', u'California', 3694820),
     (3795, u'Chicago', u'USA', u'Illinois', 2896016),
     (3796, u'Houston', u'USA', u'Texas', 1953631),
     (3797, u'Philadelphia', u'USA', u'Pennsylvania', 1517550),
     (3798, u'Phoenix', u'USA', u'Arizona', 1321045),
     (3799, u'San Diego', u'USA', u'California', 1223400),
     (3800, u'Dallas', u'USA', u'Texas', 1188580),
     (3801, u'San Antonio', u'USA', u'Texas', 1144646)]

The results are available in special local variable ``_``, and can be assigned to a variable of your
choice:

::

    In [3]: my_result = _

Pgcli only runs on Python3.6+ since 2.2.0, if you use an old version of Python,
you should use install ``pgcli <= 2.2.0``.

Thanks:
-------

A special thanks to `Jonathan Slenders <https://twitter.com/jonathan_s>`_ for
creating `Python Prompt Toolkit <http://github.com/jonathanslenders/python-prompt-toolkit>`_,
which is quite literally the backbone library, that made this app possible.
Jonathan has also provided valuable feedback and support during the development
of this app.

`Click <http://click.pocoo.org/>`_ is used for command line option parsing
and printing error messages.

Thanks to `psycopg <http://initd.org/psycopg/>`_ for providing a rock solid
interface to Postgres database.

Thanks to all the beta testers and contributors for your time and patience. :)


.. |Build Status| image:: https://api.travis-ci.org/dbcli/pgcli.svg?branch=master
    :target: https://travis-ci.org/dbcli/pgcli

.. |CodeCov| image:: https://codecov.io/gh/dbcli/pgcli/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/dbcli/pgcli
   :alt: Code coverage report

.. |Landscape| image:: https://landscape.io/github/dbcli/pgcli/master/landscape.svg?style=flat
   :target: https://landscape.io/github/dbcli/pgcli/master
   :alt: Code Health

.. |PyPI| image:: https://img.shields.io/pypi/v/pgcli.svg
    :target: https://pypi.python.org/pypi/pgcli/
    :alt: Latest Version

.. |Gitter| image:: https://badges.gitter.im/Join%20Chat.svg
    :target: https://gitter.im/dbcli/pgcli?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge
    :alt: Gitter Chat
