.. _input_hooks:


Input hooks
-----------

Input hooks are a tool for inserting an external event loop into the
prompt_toolkit event loop, so that the other loop can run as long as
prompt_toolkit is idle. This is used in applications like `IPython
<https://ipython.org/>`_, so that GUI toolkits can display their windows while
we wait at the prompt for user input.
