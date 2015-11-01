0.20.0
======

Features:
---------
* Perform auto-completion refresh in background. (Thanks: Amjith, `Darik Gamble`_, `Iryna Cherniavska`_).
  When the auto-completion entries are refreshed, the update now happens in a
  background thread. This means large databases with thousands of tables are
  handled without blocking.
* Add ``CONCURRENTLY`` to keyword completion. (Thanks: `Johannes Hoff`_).
* Add support for ``\h`` command. (Thanks: `Stuart Quin`_).
  This is a huge deal. Users can now get help on an SQL command by typing:
  ``\h COMMAND_NAME`` in the pgcli prompt.
* Add support for ``\x auto``. (Thanks: `Stuart Quin`_).
  ``\\x auto`` will automatically switch to expanded mode if the output is wider
  than the display window.
* Don't hide functions from pg_catalog. (Thanks: `Darik Gamble`_).
* Suggest set-returning functions as tables. (Thanks: `Darik Gamble`_).
  Functions that return table like results will now be suggested in places of tables. 
* Suggest fields from functions used as tables. (Thanks: `Darik Gamble`_).
* Using ``pgspecial`` as a separate module. (Thanks: `Iryna Cherniavska`_).
* Make "enter" key behave as "tab" key when the completion menu is displayed. (Thanks: `Matheus Rosa`_).
* Support different error-handling options when running multiple queries. (Thanks: `Darik Gamble`_).
  When ``on_error = STOP`` in the config file, pgcli will abort execution if one of the queries results in an error. 
* Hide the password displayed in the process name in ``ps``. (Thanks: `Stuart Quin`_)

Bug Fixes:
----------
* Fix the ordering bug in `\\d+` display, this bug was displaying the wrong table name in the reference. (Thanks: `Tamas Boros`_).
* Only show expanded layout if valid list of headers provided. (Thanks: `Stuart Quin`_).
* Fix suggestions in compound join clauses. (Thanks: `Darik Gamble`_).
* Fix completion refresh in multiple query scenario. (Thanks: `Darik Gamble`_).
* Fix the broken timing information.
* Fix the removal of whitespaces in the output. (Thanks: `Jacek Wielemborek`_)
* Fix PyPI badge. (Thanks: `Artur Dryomov`_).

Improvements:
-------------
* Move config file to `~/.config/pgcli/config` instead of `~/.pgclirc` (Thanks: `inkn`_).
* Move literal definitions to standalone JSON files. (Thanks: `Darik Gamble`_).

Internal Changes:
-----------------
* Improvements to integration tests to make it more robust. (Thanks: `Iryna Cherniavska`_).

0.19.2
======

Features:
---------

* Autocompletion for database name in \c and \connect. (Thanks: `Darik Gamble`_).
* Improved multiline query support by correctly handling open quotes. (Thanks: `Darik Gamble`_).
* Added \pager command.
* Enhanced \i to run multiple queries and display the results for each of them
* Added keywords to suggestions after WHERE clause.
* Enabled autocompletion in named queries. (Thanks: `Iryna Cherniavska`_).
* Path to .pgclirc can be specified in command line. (Thanks: `Iryna Cherniavska`_).
* Added support for pg_service_conf file. (Thanks: `Iryna Cherniavska`_).
* Added custom styles. (Contributor: `Darik Gamble`_).

Internal Changes:
-----------------

* More completer test cases. (Thanks: `Darik Gamble`_).
* Updated sqlparse version from 0.1.14 to 0.1.16. (Thanks: `Darik Gamble`_).
* Upgraded to prompt_toolkit 0.46. (Thanks: `Jonathan Slenders`_).

BugFixes:
---------
* Fixed the completer crashing on invalid SQL. (Thanks: `Darik Gamble`_).
* Fixed unicode issues, updated tests and fixed broken tests.

0.19.1
======

BugFixes:
---------

* Fix an autocompletion bug that was crashing the completion engine when unknown keyword is entered. (Thanks: `Darik Gamble`_)

0.19.0
======

Features:
---------

* Wider completion menus can be enabled via the config file. (Thanks: `Jonathan Slenders`_)

  Open the config file (~/.pgclirc) and check if you have
  ``wider_completion_menu`` option available. If not add it in and set it to
  ``True``.

* Completion menu now has metadata information such as schema, table, column, view, etc., next to the suggestions. (Thanks: `Darik Gamble`_)
* Customizable history file location via config file. (Thanks: `Çağatay Yüksel`_)

  Add this line to your config file (~/.pgclirc) to customize where to store the history file. 

::

  history_file = /path/to/history/file

* Add support for running queries from a file using ``\i`` special command. (Thanks: `Michael Kaminsky`_)

BugFixes:
---------

* Always use utf-8 for database encoding regardless of the default encoding used by the database.
* Fix for None dereference on ``\d schemaname.`` with sequence. (Thanks: `Nathan Jhaveri`_)
* Fix a crashing bug in the autocompletion engine for some ``JOIN`` queries.
* Handle KeyboardInterrupt in pager and not quit pgcli as a consequence.

Internal Changes:
-----------------

* Added more behaviorial tests (Thanks: `Iryna Cherniavska`_)
* Added code coverage to the tests. (Thanks: `Iryna Cherniavska`_)
* Run behaviorial tests as part of TravisCI (Thanks: `Iryna Cherniavska`_)
* Upgraded prompt_toolkit version to 0.45 (Thanks: `Jonathan Slenders`_)
* Update the minumum required version of click to 4.1.

0.18.0
======

Features:
---------

* Add fuzzy matching for the table names and column names. 

  Matching very long table/column names are now easier with fuzzy matching. The
  fuzzy match works like the fuzzy open in SublimeText or Vim's Ctrl-P plugin. 

  eg: Typing ``djmv`` will match `django_migration_views` since it is able to
  match parts of the input to the full table name.

* Change the timing information to seconds. 
  
  The ``Command Time`` and ``Format Time`` are now displayed in seconds instead
  of a unitless number displayed in scientific notation.

* Support for named queries (favorite queries). (Thanks: `Brett Atoms`_)

  Frequently typed queries can now be saved and recalled using a name using
  newly added special commands (``\n[+]``, ``\ns``, ``\nd``).

  eg: 

::

    # Save a query
    pgcli> \ns simple select * from foo
    saved

    # List all saved queries
    pgcli> \n+

    # Execute a saved query
    pgcli> \n simple

    # Delete a saved query
    pgcli> \nd simple

* Pasting queries into the pgcli repl is orders of magnitude faster. (Thanks: `Jonathan Slenders`_)

* Add support for PGPASSWORD environment variable to pass the password for the
  postgres database. (Thanks: `Iryna Cherniavska`_)

* Add the ability to manually refresh autocompletions by typing ``\#`` or
  ``\refresh``. This is useful if the database was updated by an external means
  and you'd like to refresh the auto-completions to pick up the new change.

Bug Fixes:
----------

* Fix an error when running ``\d table_name`` when running on a table with rules. (Thanks: `Ali Kargın`_)
* Fix a pgcli crash when entering non-ascii characters in Windows. (Thanks: `Darik Gamble`_, `Jonathan Slenders`_)
* Faster rendering of expanded mode output by making the horizontal separator a fixed length string. 
* Completion suggestions for the ``\c`` command are not auto-escaped by default. 

Internal Changes:
-----------------

* Complete refactor of handling the back-slash commands. 
* Upgrade prompt_toolkit to 0.42. (Thanks: `Jonathan Slenders`_)
* Change the config file management to use ConfigObj.(Thanks: `Brett Atoms`_)
* Add integration tests using ``behave``. (Thanks: `Iryna Cherniavska`_)
 
0.17.0
======

Features:
---------

* Add support for auto-completing view names. (Thanks: `Darik Gamble`_)
* Add support for building RPM and DEB packages. (Thanks: dp_)
* Add subsequence matching for completion. (Thanks: `Daniel Rocco`_)
  Previously completions only matched a table name if it started with the
  partially typed word. Now completions will match even if the partially typed
  word is in the middle of a suggestion.
  eg: When you type 'mig', 'django_migrations' will be suggested. 
* Completion for built-in tables and temporary tables are suggested after entering a prefix of ``pg_``. (Thanks: `Darik Gamble`_)
* Add place holder doc strings for special commands that are planned for implementation. (Thanks: `Iryna Cherniavska`_)
* Updated version of prompt_toolkit, now matching braces are highlighted. (Thanks: `Jonathan Slenders`)
* Added support of ``\\e`` command. Queries can be edited in an external editor. (Thanks: `Iryna Cherniavska`_)
  eg: When you type ``SELECT * FROM \e`` it will be opened in an external editor.
* Add special command ``\dT`` to show datatypes. (Thanks: `Darik Gamble`_)
* Add auto-completion support for datatypes in CREATE, SELECT etc. (Thanks: `Darik Gamble`_) 
* Improve the auto-completion in WHERE clause with logical operators. (Thanks: `Darik Gamble`_)
* 

Bug Fixes:
----------

* Fix the table formatting while printing multi-byte characters (Chinese, Japanese etc). (Thanks: `蔡佳男`_)
* Fix a crash when pg_catalog was present in search path. (Thanks: `Darik Gamble`_)
* Fixed a bug that broke `\\e` when prompt_tookit was updated. (Thanks: `François Pietka`_)
* Fix the display of triggers as shown in the ``\d`` output. (Thanks: `Dimitar Roustchev`_)
* Fix broken auto-completion for INNER JOIN, LEFT JOIN etc. (Thanks: `Darik Gamble`_)
* Fix incorrect super() calls in pgbuffer, pgtoolbar and pgcompleter. No change in functionality but protects against future problems. (Thanks: `Daniel Rocco`_)
* Add missing schema completion for CREATE and DROP statements. (Thanks: `Darik Gamble`_)
* Minor fixes around cursor cleanup.

0.16.3
======

Bug Fixes:
----------
* Add more SQL keywords for auto-complete suggestion.
* Messages raised as part of stored procedures are no longer ignored.
* Use postgres flavored syntax highlighting instead of generic ANSI SQL.

0.16.2
======

Bug Fixes:
----------
* Fix a bug where the schema qualifier was ignored by the auto-completion.
  As a result the suggestions for tables vs functions are cleaner. (Thanks: `Darik Gamble`_)
* Remove scientific notation when formatting large numbers. (Thanks: `Daniel Rocco`_)
* Add the FUNCTION keyword to auto-completion.
* Display NULL values as <null> instead of empty strings. 
* Fix the completion refresh when ``\connect`` is executed.

0.16.1
======

Bug Fixes:
----------
* Fix unicode issues with hstore.
* Fix a silent error when database is changed using \\c.

0.16.0
======

Features:
---------
* Add \ds special command to show sequences. 
* Add Vi mode for keybindings. This can be enabled by adding 'vi = True' in ~/.pgclirc. (Thanks: `Jay Zeng`_)
* Add a -v/--version flag to pgcli.
* Add completion for TEMPLATE keyword and smart-completion for 
  'CREATE DATABASE blah WITH TEMPLATE <tab>'. (Thanks: `Daniel Rocco`_)
* Add custom decoders to json/jsonb to emulate the behavior of psql. This
  removes the unicode prefix (eg: u'Éowyn') in the output. (Thanks: `Daniel Rocco`_)
* Add \df special command to show functions. (Thanks: `Darik Gamble`_)
* Make suggestions for special commands smarter. eg: \dn - only suggests schemas. (Thanks: `Darik Gamble`_)
* Print out the version and other meta info about pgcli at startup.

Bug Fixes:
----------
* Fix a rare crash caused by adding new schemas to a database. (Thanks: `Darik Gamble`_)
* Make \dt command honor the explicit schema specified in the arg. (Thanks: `Darik Gamble`_)
* Print BIGSERIAL type as Integer instead of Float.
* Show completions for special commands at the beginning of a statement. (Thanks: `Daniel Rocco`_)
* Allow special commands to work in a multi-statement case where multiple sql
  statements are separated by semi-colon in the same line. 

0.15.4
======
* Dummy version to replace accidental PyPI entry deletion.

0.15.3
======
* Override the LESS options completely instead of appending to it. 

0.15.2
=======
* Revert back to using psycopg2 as the postgres adapter. psycopg2cffi fails for some tests in Python 3. 

0.15.0
=======

Features:
---------
* Add syntax color styles to config.
* Add auto-completion for COPY statements.
* Change Postgres adapter to psycopg2cffi, to make it PyPy compatible. 
  Now pgcli can be run by PyPy.

Bug Fixes:
----------
* Treat boolean values as strings instead of ints.
* Make \di, \dv and \dt to be schema aware. (Thanks: `Darik Gamble`_)
* Make column name display unicode compatible. 

0.14.0
======

Features:
---------
* Add alias completion support to ON keyword. (Thanks: `Iryna Cherniavska`_)
* Add LIMIT keyword to completion. 
* Auto-completion for Postgres schemas. (Thanks: `Darik Gamble`_)
* Better unicode handling for datatypes, dbname and roles. 
* Add \timing command to time the sql commands. 
  This can be set via config file (~/.pgclirc) using `timing = True`.
* Add different table styles for displaying output. 
  This can be changed via config file (~/.pgclirc) using `table_format = fancy_grid`.
* Add confirmation before printing results that have more than 1000 rows. 

Bug Fixes:
----------

* Performance improvements to expanded view display (\x).
* Cast bytea files to text while displaying. (Thanks: `Daniel Rocco`_)
* Added a list of reserved words that should be auto-escaped.
* Auto-completion is now case-insensitive.
* Fix the broken completion for multiple sql statements. (Thanks: `Darik Gamble`_)

0.13.0
======

Features:
---------

* Add -d/--dbname option to the commandline. 
  eg: pgcli -d database
* Add the username as an argument after the database.
  eg: pgcli dbname user

Bug Fixes:
----------
* Fix the crash when \c fails.
* Fix the error thrown by \d when triggers are present.
* Fix broken behavior on \?. (Thanks: `Darik Gamble`_)

0.12.0
======

Features:
---------

* Upgrade to prompt_toolkit version 0.26 (Thanks: https://github.com/macobo) 
  * Adds Ctrl-left/right to move the cursor one word left/right respectively.
  * Internal API changes.
* IPython integration through `ipython-sql`_ (Thanks: `Darik Gamble`_)
  * Add an ipython magic extension to embed pgcli inside ipython. 
  * Results from a pgcli query are sent back to ipython. 
* Multiple sql statments in the same line separated by semi-colon. (Thanks: https://github.com/macobo)

.. _`ipython-sql`: https://github.com/catherinedevlin/ipython-sql

Bug Fixes:
----------

* Fix 'message' attribute not found exception in Python 3. (Thanks: https://github.com/GMLudo)
* Use the database username as the database name instead of defaulting to OS username. (Thanks: https://github.com/fpietka)
* Auto-completion for auto-escaped column/table names.
* Fix i-reverse-search to work in prompt_toolkit version 0.26.

0.11.0
======

Features:
---------

* Add \dn command. (Thanks: https://github.com/CyberDem0n)
* Add \x command. (Thanks: https://github.com/stuartquin)
* Auto-escape special column/table names. (Thanks: https://github.com/qwesda)
* Cancel a command using Ctrl+C. (Thanks: https://github.com/macobo)
* Faster startup by reading all columns and tables in a single query. (Thanks: https://github.com/macobo)
* Improved psql compliance with env vars and password prompting. (Thanks: `Darik Gamble`_)

Bug Fixes:
----------
* Fix the broken behavior of \d+. (Thanks: https://github.com/macobo)
* Fix a crash during auto-completion. (Thanks: https://github.com/Erethon)

Improvements:
-------------
* Faster test runs on TravisCI. (Thanks: https://github.com/macobo)
* Integration tests with Postgres!! (Thanks: https://github.com/macobo)

.. _`Darik Gamble`: https://github.com/darikg
.. _`Iryna Cherniavska`: https://github.com/j-bennet
.. _`Daniel Rocco`: https://github.com/drocco007 
.. _`Jay Zeng`:  https://github.com/jayzeng 
.. _`蔡佳男`: https://github.com/xalley
.. _dp: https://github.com/ceocoder
.. _`Jonathan Slenders`: https://github.com/jonathanslenders
.. _`Dimitar Roustchev`: https://github.com/droustchev
.. _`François Pietka`: https://github.com/fpietka
.. _`Ali Kargın`: https://github.com/sancopanco
.. _`Brett Atoms`: https://github.com/brettatoms 
.. _`Nathan Jhaveri`: https://github.com/nathanjhaveri
.. _`Çağatay Yüksel`: https://github.com/cagatay
.. _`Michael Kaminsky`: https://github.com/mikekaminsky
.. _`inkn`: inkn
.. _`Johannes Hoff`: Johannes Hoff
.. _`Matheus Rosa`: Matheus Rosa
.. _`Artur Dryomov`: https://github.com/ming13
.. _`Stuart Quin`: https://github.com/stuartquin
.. _`Tamas Boros`: https://github.com/TamasNo1
.. _`Jacek Wielemborek`: https://github.com/d33tah
