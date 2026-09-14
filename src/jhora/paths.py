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


EPHE_FILES = ("sepl_18.se1", "semo_18.se1")
EPHE_MIRROR = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"


def ephe_search_paths() -> list:
    """Where Swiss .se1 files may live, best first (user dir wins)."""
    seen = []
    for p in (user_data_dir() / "ephe",
              Path(__file__).resolve().parents[2] / "jhcore" / "ephe",
              Path.cwd() / "jhcore" / "ephe"):
        if p not in seen:
            seen.append(p)
    if is_frozen():
        bundled = resource_path("jhcore", "ephe")
        if bundled not in seen:
            seen.append(bundled)
    return seen


def ephe_available() -> Path | None:
    """First directory holding the ephemeris files, else None."""
    for p in ephe_search_paths():
        if (p / EPHE_FILES[0]).is_file():
            return p
    return None


def user_books_dir() -> Path:
    """Writable folder for user-supplied textbook .txt files."""
    return user_data_dir() / "books"


def pd_books_dir() -> Path | None:
    """Shipped public-domain seed library (always distributable).

    Resolves in repo layout, installed wheels and frozen bundles.
    """
    cands = [Path(__file__).resolve().parent / "data" / "books"]
    if is_frozen():
        cands.append(resource_path("jhora", "data", "books"))
    for c in cands:
        try:
            if c.is_dir() and any(c.glob("*.txt")):
                return c
        except Exception:
            pass
    return None


def download_ephemeris(dest: Path | None = None,
                       progress_cb=None) -> tuple:
    """Fetch the Swiss .se1 files into a user-writable directory.

    Returns (ok, message). Network errors return False, never raise.
    """
    import urllib.request
    target = Path(dest) if dest else user_data_dir() / "ephe"
    try:
        target.mkdir(parents=True, exist_ok=True)
        for i, name in enumerate(EPHE_FILES):
            out = target / name
            if out.is_file() and out.stat().st_size > 100_000:
                continue
            def _hook(done, total, _total=0, _name=name, _i=i):
                if progress_cb:
                    progress_cb(_name, done, total or 1)
            urllib.request.urlretrieve(f"{EPHE_MIRROR}/{name}", out, _hook)
            if not out.is_file() or out.stat().st_size < 100_000:
                return False, f"downloaded {name} looks corrupt"
        if progress_cb:
            progress_cb("done", 1, 1)
        return True, f"Swiss ephemeris ready in {target}"
    except Exception as e:
        return False, f"download failed: {e}"
