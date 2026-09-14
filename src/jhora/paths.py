"""Runtime paths — repository layout vs frozen (PyInstaller) bundles.

Development runs resolve data relative to the repo. Frozen executables
cannot: resources live under sys._MEIPASS (read-only) and user data must
go to a writable per-user directory. All branches that change behavior
are frozen-only; dev runs are untouched.
"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """True inside a PyInstaller bundle."""
    return bool(getattr(sys, "frozen", False))


def resource_path(*parts: str) -> Path:
    """Read-only bundled data (ephemeris, samples)."""
    if is_frozen():
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parents[2]
    return base.joinpath(*parts)


def user_data_dir(appname: str = "OpenJyotish") -> Path:
    """Writable per-user directory for the database and user files."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME",
                                   str(Path.home() / ".local" / "share")))
    return base / appname


def default_ephe_path() -> Path | None:
    """Bundled Swiss ephemeris directory, or None to keep engine defaults."""
    if not is_frozen():
        return None
    cand = resource_path("jhcore", "ephe")
    return cand if cand.is_dir() else None
