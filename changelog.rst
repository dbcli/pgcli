Current
=======

Features:
---------

* Upgrade to prompt_toolkit version 0.26 (Thanks: https://github.com/macobo) 
  * Adds Ctrl-left/right to move the cursor one word left/right respectively.
  * Internal API changes.
* IPython integration through `ipython-sql`_ (Thanks: https://github.com/darikg)
  * Add an ipython magic extension to embed pgcli inside ipython. 
  * Results from a pgcli query are sent back to ipython. 
* Multiple sql statments in the same line separated by semi-colon. (Thanks: https://github.com/macobo)

.. _`ipython-sql`: https://github.com/catherinedevlin/ipython-sql

Bug Fixes:
----------

* Fix 'message' attribute not found exception in Python 3. (Thanks: https://github.com/GMLudo)
* Use the database username as the database name instead of defaulting to OS username. (Thanks: https://github.com/fpietka)

0.11.0
======

Features:
---------

* Add \dn command. (Thanks: https://github.com/CyberDem0n)
* Add \x command. (Thanks: https://github.com/stuartquin)
* Auto-escape special column/table names. (Thanks: https://github.com/qwesda)
* Cancel a command using Ctrl+C. (Thanks: https://github.com/macobo)
* Faster startup by reading all columns and tables in a single query. (Thanks: https://github.com/macobo)
* Improved psql compliance with env vars and password prompting. (Thanks: https://github.com/darikg)

Bug Fixes:
----------
* Fix the broken behavior of \d+. (Thanks: https://github.com/macobo)
* Fix a crash during auto-completion. (Thanks: https://github.com/Erethon)

Improvements:
-------------
* Faster test runs on TravisCI. (Thanks: https://github.com/macobo)
* Integration tests with Postgres!! (Thanks: https://github.com/macobo)
