"""Shared fixtures and test data."""

from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import pytest

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.charts.varga import VargaChartComputer
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.varga import VargaLevel, VargaVariant


@pytest.fixture(scope="session", autouse=True)
def _session_db(tmp_path_factory):
    """Session/module fixture setup also stays off the repo DB.

    Higher-scoped fixtures instantiate before function-scoped autouse
    ones, so without this they would route to the default (repo) path.
    """
    from jhora.core import database as db
    db.set_db_path(tmp_path_factory.mktemp("db-session") / "session.db")
    yield
    db.close_all()
    db._db_path = None


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path):
    """Every test runs against a throwaway database.

    The file materializes only if a test actually connects, so tests
    that never touch the DB pay nothing. Tests needing the cities
    atlas seed it explicitly (see seed_cities). In-body set_db_path
    calls keep precedence; teardown resets to default routing.
    """
    from jhora.core import database as db
    db.set_db_path(tmp_path / "test.db")
    yield
    db.close_all()
    db._db_path = None


def seed_cities(db, from_path=None):
    """Bulk-copy the cities atlas into a test database."""
    import sqlite3
    if from_path is None:
        root = Path(__file__).resolve().parents[1] / "data"
        # Prefer the tracked seed (never churns); fall back to the legacy DB.
        for name in ("jhora.seed.db", "jhora.db"):
            candidate = root / name
            if candidate.is_file():
                from_path = candidate
                break
    src = sqlite3.connect(f"file:{from_path}?mode=ro", uri=True)
    try:
        rows = src.execute(
            "SELECT id, name, ascii_name, country, latitude, longitude,"
            " tz_offset FROM cities").fetchall()
    finally:
        src.close()
    db.executemany(
        "INSERT OR IGNORE INTO cities (id, name, ascii_name, country,"
        " latitude, longitude, tz_offset) VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows)
    db.commit()
    return len(rows)


# Reference birth chart (1970-04-04 17:48:20 UTC = 23:18:20 IST, Chennai)
# Used throughout the project for testing
# hour = local time (IST), tz = offset by convention: UTC = local + tz_offset
_UTC_HOUR = 17 + 48/60 + 20/3600  # 17:48:20 UTC; India = UTC+5:30
_LOCAL_HOUR = _UTC_HOUR + 5.5      # 23:18:20 IST
REF_BIRTH = dict(
    year=1970, month=4, day=4,
    hour=_LOCAL_HOUR,
    lat=13.08, lon=80.27,
    tz="-5.5", ayanamsa="lahiri",
)


def approx(val: float, ref: float, eps: float = 0.5) -> bool:
    """Check if val is within eps of ref."""
    return abs(val - ref) < eps


@pytest.fixture(scope="session")
def ref_chart() -> ChartData:
    """Build the reference chart once per session."""
    builder = ChartBuilder()
    return builder.build(**REF_BIRTH)


@pytest.fixture(scope="session")
def ref_navamsa(ref_chart):
    """Pre-compute navamsa positions for reference chart."""
    comp = VargaChartComputer()
    return comp.compute(ref_chart, VargaLevel.D_9, VargaVariant.DEFAULT)


# Expected rasi positions (approximate, sidereal Lahiri)
# Updated after Graha→SE mapping fix: planets are now correctly mapped
EXPECTED_RASI: Dict[Graha, Tuple[str, float, str]] = {
    Graha.SUN:     ("Pisces", 21.10, "neutral"),
    Graha.MOON:    ("Pisces", 1.89, "neutral"),
    Graha.MARS:    ("Aries", 26.83, "own"),
    Graha.MERCURY: ("Aries", 3.56, "neutral"),
    Graha.JUPITER: ("Libra", 9.74, "neutral"),
    Graha.VENUS:   ("Aries", 8.19, "neutral"),
    Graha.SATURN:  ("Aries", 15.12, "debilitated"),
    Graha.RAHU:    ("Aquarius", 16.88, "neutral"),
    Graha.KETU:    ("Leo", 16.88, "neutral"),
}

# Expected navamsa rasi for each planet (D-9 default, from sidereal chart)
EXPECTED_NAVAMSA: Dict[Graha, str] = {
    Graha.SUN:     "Capricorn",
    Graha.MOON:    "Cancer",
    Graha.MARS:    "Sagittarius",
    Graha.MERCURY: "Taurus",
    Graha.JUPITER: "Sagittarius",
    Graha.VENUS:   "Gemini",
    Graha.SATURN:  "Leo",
    Graha.RAHU:    "Cancer",
    Graha.KETU:    "Capricorn",
}
