"""Generate cross-check fixtures from the jyotishganit reference library.

Runs with BOTH codebases importable (system python + src/ + the isolated
venv's site-packages)::

    PYTHONPATH=src:<venv>/lib/pythonX.Y/site-packages \
        python3 tools/xcheck/generate_fixtures.py

Writes tools/xcheck/fixtures/<lib-version>/<chart-id>.json. Each fixture
carries a run header recording the reference conventions (ayanamsa value,
node assessment, house system) so diffs read against known parameters.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra",
         "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# id, year, month, day, hour, lat, lon, tz_offset(float, east+), tz_str(ours)
CHARTS = [
    ("readme-example", 1996, 7, 4, 9 + 10 / 60, 18.404, 75.195, 5.5, "+0530"),
    ("chennai-day", 2026, 7, 7, 10.5, 13.08, 80.27, 5.5, "+0530"),
    ("chennai-night", 2026, 7, 7, 2.0, 13.08, 80.27, 5.5, "+0530"),
    ("italy-1973", 1973, 3, 13, 13.0 + 55 / 60.0, 45.41, 11.88, 1.0, "+0100"),
]


def _boundary_charts():
    """Nakshatra/tithi-cusp and dawn/dusk cases, located with our ephemeris.

    Returns chart tuples like CHARTS (id, y, m, d, hour, lat, lon, tz, tzstr).
    """
    from jhora.ephemeris.swe import SweEngine, SE_SUN, SE_MOON
    swe = SweEngine()
    swe.set_sidereal_mode("lahiri")
    lat, lon, tz = 13.08, 80.27, "+0530"
    base = datetime(2026, 7, 7, 0, 0)

    def moon_lon(dt):
        gmt = dt.hour + dt.minute / 60.0 - 5.5
        return swe.calc_planet(
            SE_MOON, swe.julday(dt.year, dt.month, dt.day, gmt)).longitude

    def sun_lon(dt):
        gmt = dt.hour + dt.minute / 60.0 - 5.5
        return swe.calc_planet(
            SE_SUN, swe.julday(dt.year, dt.month, dt.day, gmt)).longitude

    out = []
    # Nakshatra cusp: first Moon crossing of a 13°20' boundary after 06:00.
    dt = base.replace(hour=6)
    prev = moon_lon(dt) // (360.0 / 27.0)
    for mins in range(5, 24 * 60, 5):
        dt = base + timedelta(minutes=mins)
        if moon_lon(dt) // (360.0 / 27.0) != prev:
            out.append(("nakshatra-cusp", dt.year, dt.month, dt.day,
                        dt.hour + dt.minute / 60.0, lat, lon, 5.5, tz))
            break
    # Tithi cusp: first Sun-Moon elongation crossing of a 12° boundary.
    prev = (moon_lon(base) - sun_lon(base)) % 360 // 12.0
    for mins in range(5, 24 * 60, 5):
        dt = base + timedelta(minutes=mins)
        if (moon_lon(dt) - sun_lon(dt)) % 360 // 12.0 != prev:
            out.append(("tithi-cusp", dt.year, dt.month, dt.day,
                        dt.hour + dt.minute / 60.0, lat, lon, 5.5, tz))
            break
    # Dawn/dusk: fixed local times near equinox sunrise/sunset.
    out.append(("dawn", 2026, 7, 7, 6.0, lat, lon, 5.5, tz))
    out.append(("dusk", 2026, 7, 7, 18.5, lat, lon, 5.5, tz))
    return out


def _skyfield_tropical(y, mo, d, hour, lat, lon, tz):
    """Apparent geocentric tropical longitudes from JPL DE421 (Skyfield).

    Independent code path from Swiss Ephemeris; the absolute-sky truth side.
    Returns {} when Skyfield/data is unavailable (fixture keeps library data).
    """
    try:
        from skyfield.api import load
        import glob
        bsp = (glob.glob(str(Path.home() / ".local/share/jyotishganit/de421.bsp"))
               or ["de421.bsp"])[0]
        ts = load.timescale()
        eph = load(bsp)
        total_min = int(round((hour - tz) * 60.0))
        t = ts.utc(y, mo, d, 0, total_min, 0)
        earth = eph["earth"]
        bodies = {"Sun": "sun", "Moon": "moon", "Mars": "mars",
                  "Mercury": "mercury", "Venus": "venus",
                  "Jupiter": "jupiter barycenter",
                  "Saturn": "saturn barycenter"}
        out = {}
        for name, target in bodies.items():
            _lat, lon_deg, _d = earth.at(t).observe(
                eph[target]).apparent().ecliptic_latlon("date")
            out[name] = round(float(lon_deg.degrees) % 360.0, 6)
        return out
    except Exception as e:
        print(f"  (skyfield unavailable: {e})")
        return {}


def _their_chart(cid, y, mo, d, hour, lat, lon, tz):
    import jyotishganit as J
    # Decimal hours -> HH:MM with rounding (int() floors 9.9999 to 9!).
    total_min = int(round(hour * 60.0))
    return J.calculate_birth_chart(
        birth_date=datetime(y, mo, d, total_min // 60, total_min % 60, 0),
        latitude=lat, longitude=lon, timezone_offset=tz, name=cid)


def _extract(chart):
    planets = []
    for p in chart.d1_chart.planets:
        try:
            sign_idx = SIGNS.index(p.sign)
        except ValueError:
            sign_idx = -1
        planets.append({
            "body": p.celestial_body,
            "sign": p.sign,
            "sign_deg": round(float(p.sign_degrees), 4),
            "abs_lon": round(sign_idx * 30.0 + float(p.sign_degrees), 4)
            if sign_idx >= 0 else None,
            "nakshatra": str(p.nakshatra),
            "pada": int(p.pada),
            "house": int(p.house),
        })
    dashas = {}
    full = getattr(chart.dashas, "all", {}) or {}
    for lord, span in list(full.get("mahadashas", {}).items()):
        ads = {}
        for alord, aspan in list(span.get("antardashas", {}).items()):
            ads[str(alord)] = {
                "start": aspan["start"].isoformat(),
                "end": aspan["end"].isoformat(),
            }
        dashas[str(lord)] = {
            "start": span["start"].isoformat(),
            "end": span["end"].isoformat(),
            "antardashas": ads,
        }
    shadbala = {}

    def _num(x):
        try:
            return round(float(x), 3)
        except (TypeError, ValueError):
            return x

    def _tree(node):
        if isinstance(node, dict):
            return {str(k): _tree(v) for k, v in node.items()}
        if isinstance(node, (list, tuple)):
            return [_tree(v) for v in node]
        return _num(node)

    for p in chart.d1_chart.planets:
        try:
            shadbala[p.celestial_body] = _tree(p.shadbala)
        except (AttributeError, TypeError):
            pass
    return {
        "planets": planets,
        "panchanga": {
            "tithi": str(chart.panchanga.tithi),
            "nakshatra": str(chart.panchanga.nakshatra),
            "yoga": str(chart.panchanga.yoga),
            "karana": str(chart.panchanga.karana),
            "vaara": str(chart.panchanga.vaara),
        },
        "dashas": dashas,
        "shadbala": shadbala,
    }


def main():
    import jyotishganit as J
    version = getattr(J, "__version__", "unknown")
    outdir = FIXTURES / version
    outdir.mkdir(parents=True, exist_ok=True)
    charts = list(CHARTS) + _boundary_charts()
    index = {"lib_version": version, "generated_at": datetime.now().isoformat(),
             "charts": []}
    for cid, y, mo, d, hour, lat, lon, tz, tzstr in charts:
        chart = _their_chart(cid, y, mo, d, hour, lat, lon, tz)
        doc = {
            "id": cid,
            "birth": {"date": f"{y:04d}-{mo:02d}-{d:02d}",
                      "hour": hour, "lat": lat, "lon": lon, "tz": tz,
                      "tz_str": tzstr},
            "ayanamsa": {"name": str(chart.ayanamsa.name),
                         "value": float(chart.ayanamsa.value)},
            "tropical": _skyfield_tropical(y, mo, d, hour, lat, lon, tz),
            "data": _extract(chart),
        }
        (outdir / f"{cid}.json").write_text(json.dumps(doc, indent=1))
        index["charts"].append(cid)
        print(f"wrote {cid}: ayanamsa={doc['ayanamsa']['value']:.4f}")
    (outdir / "index.json").write_text(json.dumps(index, indent=1))
    print(f"fixtures in {outdir}")


if __name__ == "__main__":
    main()
