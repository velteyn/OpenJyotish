#!/usr/bin/env bash

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Run ./install.sh first."
    exit 1
fi

# Launch GUI
python3 -m jhora --gui
