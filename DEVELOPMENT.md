# Development Setup

## Initial Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package in development mode with dev dependencies
pip install -e ".[dev]"
```

## Running Development Version
```bash
# Make sure you're in the virtual environment
source .venv/bin/activate

# Run the development version directly
python -m pgcli.main
```

This ensures you're running the local development version rather than any globally installed pgcli.

## Using the Pre-Execute Hook

You can add a hook that will be called before any query is executed. This allows you to inspect, modify, or prevent execution of queries. Here's an example:

```python
# Create a file called custom_pgcli.py
from pgcli.main import PGCli

def prevent_drops(query):
    """Prevent execution of DROP statements."""
    if query.strip().upper().startswith('DROP'):
        print("DROP statements are not allowed!")
        return False
    return True

# Create pgcli instance and set the hook
pgcli = PGCli()
pgcli.set_pre_execute_hook(prevent_drops)

# Run pgcli
pgcli.connect()
pgcli.run_cli()
```

Then run your custom version with optional connection parameters:
```bash
# Connect to a specific database
python custom_pgcli.py mydatabase

# Connect with host and port
python custom_pgcli.py mydatabase -h localhost -p 5432

# Connect with username
python custom_pgcli.py mydatabase -U myuser

# Show help
python custom_pgcli.py --help
```

The hook function receives the query text as a string and should return:
- `True` to allow the query to execute
- `False` to prevent the query from executing
