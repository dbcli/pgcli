A REPL for Postgres 
-------------------

This is a postgres client that does auto-completion and syntax highlighting.

.. image:: screenshots/image01.png

Installation
============

If you don't know how to install python pacakges, please check the `detailed instructions`__.

__ Detailed Installation Instructions

If you already know how to install python pacakges, then you can simply do:

::

    $ pip install pgcli


Detailed Installation Instructions:
===================================

OS X:
-----

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
------

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


Usage
=====

:: 

    $ pgcli [database_name]

    or

    $ pgcli postgresql://[user[:password]@][netloc][:port][/dbname] 

Examples: 

:: 

    $ pgcli local_database

    $ pgcli postgres://amjith:pa$$w0rd@example.com:5432/app_db


Features
========

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
