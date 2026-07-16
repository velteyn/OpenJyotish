#!/usr/bin/env bash
set -e

echo "========================================"
echo " Jagannatha Hora — Installer"
echo "========================================"
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Install Python 3.11+"
    exit 1
fi

echo "Python: $(python3 --version)"
echo

# Create venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt
pip install -e .

echo
echo "========================================"
echo " Setup complete!"
echo "========================================"
echo
echo "Commands:"
echo "  ./run.sh            Launch GUI"
echo "  jhora tui           Terminal mode"
echo "  jhora chart --help  See all CLI commands"
echo
