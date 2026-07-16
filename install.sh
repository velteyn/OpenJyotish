#!/usr/bin/env bash
set -e

echo "========================================"
echo " Jagannatha Hora — Installer"
echo "========================================"
echo

# Find Python
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0")
        major=$(echo "$ver" | cut -d. -f1)
        if [ "$major" -ge 3 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3 not found. Install Python 3.11+ from python.org"
    exit 1
fi

echo "Python: $($PYTHON --version)"
echo

# Check version
$PYTHON -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" || {
    echo "ERROR: Python 3.11+ required."
    exit 1
}

# Create venv
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv venv || {
        echo "ERROR: Could not create venv. Try: $PYTHON -m pip install virtualenv"
        exit 1
    }
    echo "Virtual environment created."
else
    echo "Virtual environment exists (venv/)"
fi

echo

# Verify activate exists
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: venv/bin/activate not found. Recreate with: rm -rf venv && ./install.sh"
    exit 1
fi

# Activate
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip -q 2>/dev/null || true
pip install -r requirements.txt
pip install -e . 2>/dev/null || pip install -e . --break-system-packages 2>/dev/null || {
    echo "WARNING: pip install -e . had issues."
    echo "You may need: pip install --break-system-packages -e ."
}

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
