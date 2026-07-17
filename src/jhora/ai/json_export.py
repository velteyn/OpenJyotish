"""AI-friendly JSON exporter — single command to dump all chart analysis."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from jhora.charts.chart import ChartBuilder, ChartData
from jhora.calc.shadbala import ShadbalaComputer
from jhora.calc.bhava_bala import BhavaBalaComputer
from jhora.calc.vimsopaka import VimsopakaComputer, VimsopakaScheme
from jhora.calc.yogas import detect_all
from jhora.calc.gochara import compute_transits
from jhora.calc.karaka import compute_chara_karakas
from jhora.calc.arudha import all_bhava_arudhas
from jhora.calc.ashtakavarga import sarva_ashtakavarga
from jhora.calc.upagraha import compute_solar_upagrahas
from jhora.calc.special_lagnas import compute_special_lagnas, kp_sublord_string
from jhora.calc.learning import marana_karaka_sthana, vaiseshikamsas, ishta_kashta_phala
from jhora.dasas.vimsottari import VimsottariDasa
from jhora.ephemeris.swe import SweEngine
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi
from jhora.types.nakshatra import Nakshatra


def full_analysis(birthdata: str, ayanamsa: str = "lahiri") -> Dict[str, Any]:
    """Compute everything and return as a structured JSON dict."""
    from jhora.cli.main import parse_birthdata as _parse
    bd = _parse(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    return chart_to_json(cd)


def chart_to_json(cd: ChartData) -> Dict[str, Any]:
    now = datetime.now()
    result: Dict[str, Any] = {}

    # ── Meta ──
    lr = Rasi.from_longitude(cd.ascendant)
    result["meta"] = {
        "birth_date": cd.birth_date.strftime("%Y-%m-%d %H:%M"),
        "julian_day": round(cd.julian_day, 6),
        "latitude": "[REDACTED]",
        "longitude": "[REDACTED]",
        "timezone": cd.timezone,
        "ayanamsa": cd.ayanamsa_name,
        "ayanamsa_value": round(cd.ayanamsa_value, 4),
        "lagna": {"sign": lr.full_name, "short": lr.short_name,
                   "longitude": round(cd.ascendant, 4)},
    }

    # ── Planets ──
    result["planets"] = {}
    for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
              Graha.JUPITER, Graha.VENUS, Graha.SATURN, Graha.RAHU, Graha.KETU]:
        p = cd.planet(g)
        r = Rasi.from_longitude(p.longitude)
        n, pada = Nakshatra.from_longitude(p.longitude)
        h = ((int(p.longitude / 30) - int(cd.ascendant / 30)) % 12) + 1
        result["planets"][g.short_name] = {
            "name": g.full_name,
            "longitude": round(p.longitude, 4),
            "sign": r.full_name,
            "sign_short": r.short_name,
            "house": h,
            "lord": r.lord,
            "nakshatra": n.name.replace("_", " ").title(),
            "nakshatra_pada": pada,
            "retrograde": p.is_retrograde,
            "dignity": p.dignity,
        }

    # ── Houses ──
    result["houses"] = {}
    for h in range(12):
        cusp = cd.house_cusps[h]
        r = Rasi.from_longitude(cusp)
        result["houses"][str(h + 1)] = {
            "cusp": round(cusp, 4),
            "sign": r.full_name,
            "sign_short": r.short_name,
            "lord": r.lord,
        }

    # ── Shadbala ──
    try:
        sb = ShadbalaComputer(cd)
        result["shadbala"] = {}
        for g in [Graha.SUN, Graha.MOON, Graha.MARS, Graha.MERCURY,
                  Graha.JUPITER, Graha.VENUS, Graha.SATURN]:
            r = sb.compute_one(g)
            result["shadbala"][g.short_name] = {
                "sthana": round(r.sthana_total, 1),
                "dig": round(r.dig_total, 1),
                "kala": round(r.kala_total, 1),
                "chesta": round(r.chesta_total, 1),
                "naisargika": round(r.naisargika.virupa, 1),
                "drik": round(r.drik.virupa, 1),
                "total_virupas": round(r.total_virupa, 0),
                "total_rupas": round(r.total_rupa, 2),
            }
    except Exception:
        result["shadbala"] = {}

    # ── Bhava Bala ──
    try:
        bb = BhavaBalaComputer(cd)
        report = bb.compute_all()
        result["bhava_bala"] = {}
        for h in range(1, 13):
            r = report.results[h]
            ri = (int(cd.ascendant / 30) + h - 1) % 12
            result["bhava_bala"][str(h)] = {
                "sign": Rasi(ri).short_name,
                "sthana": round(r.sthana, 1),
                "drishti": round(r.drishti, 1),
                "dig": round(r.dig, 1),
                "adhipati": round(r.adhipati, 1),
                "drig": round(r.drig, 1),
                "total": round(r.total, 1),
            }
    except Exception:
        result["bhava_bala"] = {}

    # ── Vimsopaka ──
    try:
        vc = VimsopakaComputer(cd)
        result["vimsopaka"] = {}
        for r in vc.compute_all(VimsopakaScheme.SHADVARGA):
            result["vimsopaka"][r.graha.short_name] = {
                "score": r.total,
                "percentage": r.percentage,
            }
    except Exception:
        result["vimsopaka"] = {}

    # ── Yogas ──
    try:
        yogas = detect_all(cd)
        result["yogas"] = [{"name": y.name, "planets": [p.short_name for p in (y.planets or [])],
                            "description": y.description[:100]} for y in yogas]
    except Exception:
        result["yogas"] = []

    # ── Dasa ──
    try:
        dasa = VimsottariDasa()
        cd_dict = {"planets": {g.value: {"longitude": p.longitude}
                               for g, p in cd.planets.items()},
                   "lagna_lon": cd.ascendant}
        periods = dasa.compute(cd.julian_day, cd_dict)
        result["dasa"] = {"mahadashas": []}
        for md in periods:
            md_data = {
                "lord": md.lord_name,
                "start": md.start_date.strftime("%Y-%m-%d"),
                "end": md.end_date.strftime("%Y-%m-%d"),
                "years": round(md.duration_years, 1),
                "current": md.start_date <= now <= md.end_date,
            }
            if md.start_date <= now <= md.end_date:
                md_data["antardashas"] = []
                for ad in (md.sub_periods or []):
                    ad_current = ad.start_date <= now <= ad.end_date
                    md_data["antardashas"].append({
                        "lord": ad.lord_name,
                        "start": ad.start_date.strftime("%Y-%m-%d"),
                        "end": ad.end_date.strftime("%Y-%m-%d"),
                        "current": ad_current,
                    })
            result["dasa"]["mahadashas"].append(md_data)
    except Exception:
        result["dasa"] = {}

    # ── Transits ──
    try:
        eng = SweEngine()
        jd = eng.julday(now.year, now.month, now.day, now.hour + now.minute / 60.0)
        tr = compute_transits(cd, jd)
        result["transits"] = []
        for e in tr.entries:
            result["transits"].append({
                "planet": e.graha.short_name if hasattr(e.graha, 'short_name') else str(e.graha),
                "sign": e.transit_rasi_name,
                "house": e.house_from_lagna,
                "sav": e.sav_score,
                "favorable": e.is_favorable,
            })
    except Exception:
        result["transits"] = []

    # ── Karakas ──
    try:
        cks = compute_chara_karakas(cd.planets)
        result["karakas"] = [{"planet": ck.graha.short_name, "karaka": ck.short_name} for ck in cks]
    except Exception:
        result["karakas"] = []

    # ── Upagrahas ──
    try:
        sun_lon = cd.planet(Graha.SUN).longitude
        upas = compute_solar_upagrahas(sun_lon)
        result["upagrahas"] = [{"name": u.name, "sign": u.rasi, "longitude": round(u.longitude, 2)} for u in upas]
    except Exception:
        result["upagrahas"] = []

    # ── Special Lagnas ──
    try:
        sl = compute_special_lagnas(cd)
        result["special_lagnas"] = [{"name": s.name, "sign": s.sign, "longitude": round(s.longitude, 2),
                                      "description": s.description} for s in sl]
    except Exception:
        result["special_lagnas"] = []

    # ── KP ──
    result["kp_sublords"] = {}
    try:
        for g in Graha:
            if g in cd.planets:
                result["kp_sublords"][g.short_name] = kp_sublord_string(cd.planet(g).longitude, 3)
    except Exception:
        pass

    # ── Marana Karaka ──
    try:
        mk = marana_karaka_sthana(cd)
        result["marana_karaka"] = [{"planet": m["graha"], "house": m["house"], "sign": m["sign"]} for m in mk]
    except Exception:
        result["marana_karaka"] = []

    # ── Vaiseshikamsas ──
    try:
        va = vaiseshikamsas(cd)
        result["vaiseshikamsas"] = [{"planet": v["graha"], "score": v["score"], "rank": v["rank"]} for v in va]
    except Exception:
        result["vaiseshikamsas"] = []

    # ── Ashtakavarga ──
    try:
        sav = sarva_ashtakavarga(cd)
        result["ashtakavarga"] = {"sav": {Rasi(i).short_name: int(sav[i]) for i in range(12)},
                                  "total": int(sum(sav))}
    except Exception:
        result["ashtakavarga"] = {}

    return result
