#!/usr/bin/env bash

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found."
    echo "Run ./install.sh first."
    exit 1
fi

python -m jhora --gui 2>/dev/null || python3 -m jhora --gui
