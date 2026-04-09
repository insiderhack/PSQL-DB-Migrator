#!/bin/bash
# Activate virtual environment and run PG Migrator

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if venv exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Run the application
PYTHONPATH="$SCRIPT_DIR/src" python -m pg_migrator.main "$@"
