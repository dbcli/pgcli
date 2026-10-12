Pgclirc parser compatibility
============================

Pgcli uses :mod:`configparser` for the section and option structure of its main
``pgclirc`` file, with a small compatibility layer for the ConfigObj syntax
used by existing files.  Unlike an unconfigured ``configparser`` instance, the
adapter keeps option names case-sensitive, disables ``%`` interpolation, treats
``[DEFAULT]`` as an ordinary section, removes matching outer quotes, and exposes
ConfigObj-compatible boolean, integer, and comma-separated list accessors.

Quoted values may contain literal ``#`` and ``%`` characters.  Inline ``#``
comments, user comments, and layout are retained when settings or named queries
are written.  Both ConfigObj triple-quote styles are accepted for multiline
values; their blank lines, comment-prefixed lines, indentation, and surrounding
whitespace are preserved.  New multiline values are written with triple quotes.
Default-file values are loaded first and user-file values override them.

Pgclirc supports single-bracket sections, including dotted names such as
``[alias_dsn.init-commands]``.  ConfigObj root-level options and nested
``[[sections]]`` are intentionally unsupported and produce a clear error rather
than being silently reinterpreted.  ConfigObj remains a runtime dependency for
PostgreSQL service-file parsing until that separate consumer is migrated.
