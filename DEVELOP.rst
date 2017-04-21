Development Guide
-----------------
This is a guide for developers who would like to contribute to this project.

GitHub Workflow
------------

If you're interested in contributing to pgcli, first of all my heart felt
thanks. `Fork the project <https://github.com/dbcli/pgcli>`_ in github.  Then
clone your fork into your computer (``git clone <url-for-your-fork>``).  Make
the changes and create the commits in your local machine. Then push those
changes to your fork. Then click on the pull request icon on github and create
a new pull request. Add a description about the change and send it along. I
promise to review the pull request in a reasonable window of time and get back
to you.

In order to keep your fork up to date with any changes from mainline, add a new
git remote to your local copy called 'upstream' and point it to the main pgcli
repo.

::

   $ git remote add upstream git@github.com:dbcli/pgcli.git

Once the 'upstream' end point is added you can then periodically do a ``git
pull upstream master`` to update your local copy and then do a ``git push
origin master`` to keep your own fork up to date.

Local Setup
-----------

The installation instructions in the README file are intended for users of
pgcli. If you're developing pgcli, you'll need to install it in a slightly
different way so you can see the effects of your changes right away without
having to go through the install cycle everytime you change the code.

It is highly recommended to use virtualenv for development. If you don't know
what a virtualenv is, this `guide <http://docs.python-guide.org/en/latest/dev/virtualenvs/#virtual-environments>`_
will help you get started.

Create a virtualenv (let's call it pgcli-dev). Activate it:

::

    source ./pgcli-dev/bin/activate

Once the virtualenv is activated, `cd` into the local clone of pgcli folder
and install pgcli using pip as follows:

::

    $ pip install --editable .

    or

    $ pip install -e .

This will install the necessary dependencies as well as install pgcli from the
working folder into the virtualenv. By installing it using `pip install -e`
we've linked the pgcli installation with the working copy. So any changes made
to the code is immediately available in the installed version of pgcli. This
makes it easy to change something in the code, launch pgcli and check the
effects of your change.

Adding PostgreSQL Special (Meta) Commands
-----------------------------------------

If you want to work on adding new meta-commands (such as `\dp`, `\ds`, `dy`),
you'll be changing the code of `packages/pgspecial.py`. Search for the
dictionary called `CASE_SENSITIVE_COMMANDS`. The special command us used as
the dictionary key, and the value is a tuple.

The first item in the tuple is either a string (sql statement) or a function.
The second item in the tuple is a list of strings which is the documentation
for that special command. The list will have two items, the first item is the
command itself with possible options and the second item is the plain english
description of that command.

For example, `\l` is a meta-command that lists all the databases. The way you
can see the SQL statement issued by PostgreSQL when this command is executed
is to launch `psql -E` and entering `\l`.

That will print the results and also print the sql statement that was executed
to produce that result. In most cases it's a single sql statement, but sometimes
it's a series of sql statements that feed the results to each other to get to
the final result.

Building RPM and DEB packages
-----------------------------

You will need Vagrant 1.7.2 or higher. In the project root there is a
Vagrantfile that is setup to do multi-vm provisioning. If you're setting things
up for the first time, then do:

::

    $ version=x.y.z vagrant up debian
    $ version=x.y.z vagrant up centos

If you already have those VMs setup and you're merely creating a new version of
DEB or RPM package, then you can do:

::

    $ version=x.y.z vagrant provision

That will create a .deb file and a .rpm file.

The deb package can be installed as follows:

::

    $ sudo dpkg -i pgcli*.deb   # if dependencies are available.

    or

    $ sudo apt-get install -f pgcli*.deb  # if dependencies are not available.


The rpm package can be installed as follows:

::

    $ sudo yum install pgcli*.rpm

Running the integration tests
-----------------------------

Integration tests use `behave package http://pythonhosted.org/behave/`_ and
pytest.
Configuration settings for this package are provided via ``behave.ini`` file
in the ``tests`` directory.

The database user (``pg_test_user = postgres`` in .ini file) has to have
permissions to create and drop test database. Default user is ``postgres``
at ``localhost``, without the password (authentication mode trust).

First, install the requirements for testing:

::

    $ pip install -r requirements-dev.txt

After that, tests can be run with:

::

    $ cd tests
    $ behave
    $ py.test

To see stdout/stderr, use the following command:

::

    $ behave --no-capture


PEP8 checks
-----------

When you submit a PR, the changeset is checked for pep8 compliance using
`pep8radius <https://github.com/hayd/pep8radius>`_. If you see a build failing because
of these checks, install pep8radius and apply style fixes:

::

    $ pip install pep8radius
    $ pep8radius --docformatter --diff # view a diff of proposed fixes
    $ pep8radius --docformatter --in-place # apply the fixes

Then commit and push the fixes.
