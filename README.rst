** WIP - DO NOT USE **

A REPL for Postgres 
-------------------

This is a postgres client that does auto-completion and syntax highlighting.

.. image:: screenshots/image02.png
.. image:: screenshots/image01.png

Quick Start
-----------

If you already know how to install python pacakges, then you can simply do:

::

    $ pip install pgcli

If you don't know how to install python pacakges, please check the `detailed instructions`__.

__ https://github.com/amjith/pgcli#detailed-installation-instructions 

Usage
-----

:: 

    $ pgcli [database_name]

    or

    $ pgcli postgresql://[user[:password]@][netloc][:port][/dbname] 

Examples: 

:: 

    $ pgcli local_database

    $ pgcli postgres://amjith:pa$$w0rd@example.com:5432/app_db

Features
--------

The `pgcli` is written using prompt_toolkit_.

* Auto-completion as you type for SQL keywords as well as tables and
  columns in the database.
* Syntax highlighting using Pygments.
* Smart-completion (enabled by default) will suggest context-sensitive completion.

      - `SELECT * FROM <tab>` will only show table names. 
      - `SELECT * FROM users WHERE <tab>` will only show column names. 

* Config file is automatically created at ~/.pglirc at first launch.
* Primitive support for `psql` back-slash commands. 

.. _prompt_toolkit: https://github.com/jonathanslenders/python-prompt-toolkit

Detailed Installation Instructions:
-----------------------------------

OS X:
=====

For installing Python pacakges it is recommended to use the package manager
called `pip`. Check if `pip` is installed on the system.

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

Check if pip is already available in your system.

:: 

    $ which pip

If it does then install pgcli using the pip command as follows:

:: 

    $ sudo pip install pgcli

If it doesn't exist, use your linux package manager to install `pip`. This might look something like: 

::

    $ sudo apt-get install python-pip

    or

    $ sudo yum install python-pip

Then you can install pgcli: 

:: 

    $ sudo pip install pgcli


Gratitude:
==========

A special thanks to Jonathan Slenders for creating Python Prompt Toolkit, which
is quite literally the backbone library that made this app possible. Jonathan
has also provided valuable feedback and support during the development of this
app.

This app also includes tabulate (https://pypi.python.org/pypi/tabulate) library
for printing the output of the tables. The reason for copying it directly and
not listing it as a dependency is because I had to make a change to the table
format which is merged back into the original repo, but not yet released in
PyPI.

Click is used for command line option parsing and printing error messages.

Thanks to psycopg2 for providing a rock solid interface to Postgres dataabase.
