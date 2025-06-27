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
