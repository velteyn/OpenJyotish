#!/usr/bin/env bash

[ -f "venv/bin/activate" ] && source venv/bin/activate || {
    echo "venv not found. Run ./install.sh first."
    exit 1
}

# Try jhora CLI first, then fall back to python -m
jhora --gui 2>/dev/null && exit 0
python3 -m jhora --gui 2>/dev/null && exit 0
python -m jhora --gui 2>/dev/null && exit 0

echo "Could not launch GUI. Try: source venv/bin/activate && python3 -m jhora --gui"
exit 1
