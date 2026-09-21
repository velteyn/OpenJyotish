"""GUI entry for frozen builds: `openjyotish --gui` without flag parsing."""
import sys

sys.argv = [sys.argv[0], "--gui"]

from jhora.__main__ import main

main()
