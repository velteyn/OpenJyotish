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
        ver=$("$cmd" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
        if [ "$ver" -ge 3 ]; then
            PYTHON="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3 not found."
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
    echo "Creating virtual environment (method 1: venv)..."
    if $PYTHON -m venv venv 2>/dev/null; then
        echo "Virtual environment created."
    else
        echo "venv failed (missing python3-venv package?)."
        echo "Trying method 2: virtualenv..."
        $PYTHON -m pip install virtualenv --break-system-packages -q 2>/dev/null || \
            $PYTHON -m pip install virtualenv -q 2>/dev/null || true
        if $PYTHON -m virtualenv venv 2>/dev/null; then
            echo "Virtual environment created via virtualenv."
        else
            echo ""
            echo "ERROR: Could not create virtual environment."
            echo ""
            echo "Fix (Ubuntu/Debian):"
            echo "  sudo apt install python3-venv python3-pip"
            echo "  or: sudo apt install python3.14-venv"
            echo ""
            echo "Fix (any Linux):"
            echo "  pip install virtualenv --break-system-packages"
            echo "  python3 -m virtualenv venv"
            exit 1
        fi
    fi
else
    echo "Virtual environment exists (venv/)"
fi

# Verify activate exists
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: venv/bin/activate not found. Recreate with: rm -rf venv && ./install.sh"
    exit 1
fi

# Activate
source venv/bin/activate

echo
echo "Installing dependencies..."
pip install --upgrade pip -q 2>/dev/null || true

# Install deps — try normal first, then --break-system-packages
pip install -r requirements.txt 2>/dev/null || \
    pip install -r requirements.txt --break-system-packages 2>/dev/null || {
    echo "ERROR: Could not install dependencies."
    exit 1
}

pip install -e . 2>/dev/null || \
    pip install -e . --break-system-packages 2>/dev/null || {
    echo "WARNING: pip install -e . had issues, but deps are installed."
    echo "You can still run: python3 -m jhora --gui"
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
