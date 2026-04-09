#!/bin/bash
# PG Migrator - GUI Launcher
# One-click open application script for the graphical user interface

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if venv exists, create it and install dependencies if not
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo "First time setup: Creating virtual environment and installing dependencies..."
    python3 -m venv "$SCRIPT_DIR/venv"
    source "$SCRIPT_DIR/venv/bin/activate"
    pip install --upgrade pip
    pip install -r "$SCRIPT_DIR/requirements.txt"
    echo "Setup complete!"
else
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Set the Python path to include the src directory
export PYTHONPATH="$SCRIPT_DIR/src"

# Check if customtkinter is installed, install if missing
python -c "import customtkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required GUI dependency (customtkinter)..."
    pip install customtkinter>=5.2.2
fi

echo "Launching PG Migrator GUI..."
# Run the GUI application in the background
python -m pg_migrator.main gui &

# Optional: if you want the terminal to close automatically after launching on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    exit 0
fi