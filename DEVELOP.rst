Development Guide
-----------------
This is a guide for developers who would like to contribute to this project.

Git Workflow
------------

If you're interested in contributing to pgcli, first of all my heart felt
thanks. Please `fork the project <https://github.com/amjith/pgcli>`_ in github.
Then clone your fork into your computer (``git clone <url-for-your-fork>``).
Make the necessary changes and create the commits in your local machine. Then
push those changes to your fork. Then click on the pull request icon on github
and create a new pull request. Add a description about the change and send it
along. I promise to review you in a reasonable window of time and get back to
you. 

In order to keep your fork up to date with any changes from mainline, add a new
git remote to your local copy called 'upstream' and point it to the main pgcli
repo.

.. :: 

   $ git remote add upstream git@github.com:amjith/pgcli.git

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

Create a virtualenv (let's call it pgcli-dev). Once the virtualenv is activated
`cd` into the local clone of pgcli folder and install pgcli using pip as
follows:

.. ::

    $ pip install --editable .

    or

    $ pip install -e .

This will install the necessary dependencies as well as install pgcli from the
working folder into the virtualenv. By installing it using `pip install -e`
we've linked the pgcli installation with the working copy. So any changes made
to the code is immediately available in the installed version of pgcli. This
makes it easy to change something in the code, launch pgcli and check the
effects of your change. 
