"""GUI entry for frozen builds: `jhora --gui` without flag parsing."""
import sys

sys.argv = [sys.argv[0], "--gui"]

from jhora.__main__ import main

main()
