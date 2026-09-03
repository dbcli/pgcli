# Copilot instructions for pgcli

## Project overview

pgcli is a Python 3.10+ interactive PostgreSQL client. The executable entry
point is `pgcli.main:cli` (also available as `python -m pgcli`) and the
interactive REPL is implemented by `PGCli` in `pgcli/main.py`.

The main runtime flow is:

- `pgcli.main.PGCli` loads configuration, creates the prompt-toolkit session,
  dispatches SQL and psql-style commands, handles transactions and output, and
  coordinates the other components.
- `pgcli.pgexecute.PGExecute` owns psycopg connections and PostgreSQL queries.
  Its metadata methods provide schemas, relations, columns, functions,
  datatypes, search paths, and other information used by completion.
- `pgcli.completion_refresher.CompletionRefresher` populates a new
  `PGCompleter` in a background thread (using a copied connection unless
  single-connection mode is enabled). Keep callback and connection-lifecycle
  behavior intact when changing completion refreshes.
- `pgcli.pgcompleter.PGCompleter` turns metadata and query history into
  prompt-toolkit completions. `pgcli/packages/sqlcompletion.py` and
  `pgcli/packages/parseutils/` determine SQL context, tables, aliases, CTEs,
  and partial identifiers; changes to parsing often affect both completion
  behavior and its tests.
- PostgreSQL backslash/meta-command behavior is supplied by the
  `pgspecial` dependency. Local `pgcli/packages/` code adds SQL formatting,
  parsing, prompt utilities, and bundled PostgreSQL literal/completion data.
- `pgcli/config.py` merges the packaged `pgcli/pgclirc` defaults with the
  user config under the platform config directory. Tests redirect
  `XDG_CONFIG_HOME` so they do not use a developer's real configuration.

## Development setup and commands

Use `uv` and an editable install for development:

```sh
uv venv
source .venv/bin/activate
uv pip install -e '.[dev]'
```

The CI setup uses a synced environment, which is also convenient locally:

```sh
uv sync --all-extras
```

Run the unit test suite:

```sh
uv run pytest
```

Run one test or a focused subset with pytest's node IDs:

```sh
uv run pytest tests/test_config.py::test_name
uv run pytest tests/test_pgexecute.py -k "connection"
```

The tox environments used by CI are:

```sh
uv run tox -e py             # pytest with coverage, then coverage report
uv run tox -e style          # ruff check and format diff
uv run tox -e rest           # validate changelog.rst as ReStructuredText
uv run tox -e integration    # Behave PostgreSQL integration tests
```

Integration tests need a reachable PostgreSQL server and a user able to
create/drop the test database. They read `PGHOST`, `PGPORT`, `PGUSER`, and
`PGPASSWORD`; the default is localhost, port 5432, user `postgres`. Run all
features with:

```sh
uv run behave tests/features --no-capture
```

Run one feature or scenario with:

```sh
uv run behave tests/features/basic_commands.feature --no-capture
uv run behave tests/features/basic_commands.feature -n "scenario name" --no-capture
```

The CI integration job also starts PostgreSQL 10 and pgbouncer. Scenarios
tagged for pgbouncer require a pgbouncer listener on port 6432; scenarios
requiring unavailable database features are skipped by the test helpers.

## Code and test conventions

- Follow the Ruff configuration in `pyproject.toml`: line length 140, preview
  formatting, preserved quote style, and the configured lint rule set. The
  formatter intentionally excludes some legacy modules (`magic.py` and
  `pyev.py`); do not reformat those files incidentally.
- This project uses psycopg 3 APIs. Preserve the existing connection parameter
  precedence and error-handling behavior in `PGExecute`, especially DSNs,
  environment variables, SSH tunnel parameters, connect timeouts, and the
  separate completion connection.
- PostgreSQL metadata is cached in completer structures keyed by escaped
  schema/table names. Use the existing identifier escaping and parsing helpers
  rather than introducing ad-hoc quoting or lowercasing.
- Prompt-toolkit callbacks and completion refreshes may run on background
  threads. UI updates should go through the existing callback flow, and copied
  executors must be closed when a refresh finishes.
- Unit tests live in `tests/test_*.py` and use fixtures from `tests/conftest.py`
  and `tests/utils.py`. Database-dependent tests use the shared connection
  fixtures/skip markers; keep tests isolated because fixtures reset the public
  schema after each test.
- Interactive behavior is covered by Gherkin files in `tests/features/` and
  Python step definitions in `tests/features/steps/`. The Behave environment
  creates a version-specific temporary database, temporary config home, and
  controlled pager/editor environment; do not make feature tests depend on a
  developer's global config or terminal settings.
- Configuration defaults belong in `pgcli/pgclirc`; configuration parsing and
  precedence belong in `pgcli/config.py`. Avoid reading or writing the user's
  real config from tests.
- User-visible changes should be recorded in `changelog.rst`. Pull requests
  follow `.github/PULL_REQUEST_TEMPLATE.md`, including the changelog and
  verification checklist.
