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


def full_analysis(birthdata: str, ayanamsa: str = "lahiri",
                  usl_config=None) -> Dict[str, Any]:
    """Compute everything and return as a structured JSON dict.

    usl_config: optional UserSpecialLagnaConfig to include a USL entry.
    """
    from jhora.cli.main import parse_birthdata as _parse
    bd = _parse(birthdata)
    builder = ChartBuilder()
    builder.swe.set_sidereal_mode(ayanamsa)
    cd = builder.build(
        year=bd["year"], month=bd["month"], day=bd["day"],
        hour=bd["hour"], lat=bd["lat"], lon=bd["lon"],
        tz=bd["tz"], ayanamsa=ayanamsa,
    )
    return chart_to_json(cd, usl_config=usl_config)


def chart_to_json(cd: ChartData, usl_config=None) -> Dict[str, Any]:
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
        result["dasa"] = {"system": "vimsottari",
                          "options": {"seed": "moon", "sesham": "moon",
                                      "year": "solar"},
                          "mahadashas": []}
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

        # Other dasa systems: current mahadasha ruler in each available system.
        from jhora.ai.analysis import _dasa_engine
        result["dasa"]["systems"] = {}
        for sys in ("ashtottari", "yogini", "sudasa", "chara",
                    "narayana", "kalachakra", "brahma"):
            try:
                periods = _dasa_engine(sys).compute(cd.julian_day, cd_dict)
                for p in periods:
                    if p.start_date <= now <= p.end_date:
                        result["dasa"]["systems"][sys] = {
                            "current_mahadasha_lord": p.lord_name,
                            "start": p.start_date.strftime("%Y-%m-%d"),
                            "end": p.end_date.strftime("%Y-%m-%d"),
                        }
                        break
            except Exception:
                result["dasa"]["systems"][sys] = {}
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
        planets = {g: {"longitude": p.longitude, "speed": p.speed}
                   for g, p in cd.planets.items()}
        cks = compute_chara_karakas(planets)
        result["karakas"] = [{"planet": ck.graha.short_name, "karaka": ck.short_name} for ck in cks]
    except Exception:
        result["karakas"] = []

    # ── Arudhas (bhava + graha) ──
    try:
        from jhora.calc.arudha import all_bhava_arudhas, all_graha_arudhas
        bhava = all_bhava_arudhas(cd.ascendant, planets)
        graha_arus = all_graha_arudhas(planets)
        pada_names = {1: "AL", 2: "A2 (Dhana)", 3: "A3 (Vikrama)", 4: "A4 (Sukha)",
                      5: "A5 (Mantra)", 6: "A6 (Satru)", 7: "A7 (Dara)", 8: "A8 (Mrityu)",
                      9: "A9 (Bhagya)", 10: "A10 (Karma)", 11: "A11 (Labha)",
                      12: "A12 (Upapada)"}
        result["arudhas"] = {
            "bhava": [{"house": n, "pada": pada_names[n], "sign": bhava[n].short_name}
                      for n in range(1, 13)],
            "graha": [{"planet": g.short_name,
                       "sign": graha_arus[g].short_name}
                      for g in Graha if g in graha_arus],
        }
    except Exception:
        result["arudhas"] = {}

    # ── Sahamas ──
    try:
        from jhora.calc.sahama import compute_sahamas
        is_day = 6.0 <= cd.time_of_day_hours < 18.0
        sahamas = compute_sahamas(cd.ascendant, planets, day=is_day)
        result["sahamas"] = [{
            "name": s.name,
            "meaning": s.meaning,
            "longitude": round(s.longitude, 2),
            "sign": Rasi(int(s.longitude / 30)).short_name,
        } for s in sahamas]
    except Exception:
        result["sahamas"] = []

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

    # User's Special Lagna (optional)
    if usl_config is not None:
        try:
            from jhora.calc.special_lagnas import user_special_lagna, user_special_lagna_name
            usl_lon = user_special_lagna(cd, usl_config.planet,
                                         usl_config.speed_factor, usl_config.reverse)
            if usl_lon is not None:
                result["special_lagnas"].append({
                    "name": user_special_lagna_name(usl_config),
                    "sign": Rasi.from_longitude(usl_lon).short_name,
                    "longitude": round(usl_lon, 2),
                    "description": (f"User's Special Lagna "
                                    f"({usl_config.planet.full_name} × {usl_config.speed_factor})"),
                })
        except Exception:
            pass

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

    # ── Kuja Dosha ──
    try:
        from jhora.calc.kuja_dosha import compute_kuja_dosha
        kd = compute_kuja_dosha(cd)
        result["kuja_dosha"] = {
            "present": kd.has_dosha,
            "from_lagna": {"house": kd.mars_from_lagna_house, "afflicted": kd.from_lagna},
            "from_moon": {"house": kd.mars_from_moon_house, "afflicted": kd.from_moon},
            "from_venus": {"house": kd.mars_from_venus_house, "afflicted": kd.from_venus},
            "mars_sign": kd.mars_sign,
            "mars_own_sign": kd.mars_own_sign,
            "jupiter_cancels": kd.jupiter_cancels,
            "lagna_cancels": kd.lagna_cancels,
            "lagna_name": kd.lagna_name,
            "messages": kd.messages,
        }
    except Exception:
        result["kuja_dosha"] = {}

    # ── Ashtakavarga ──
    try:
        sav = sarva_ashtakavarga(cd)
        result["ashtakavarga"] = {"sav": {Rasi(i).short_name: int(sav[i]) for i in range(12)},
                                  "total": int(sum(sav))}
    except Exception:
        result["ashtakavarga"] = {}

    # ── Choghadiya (day/night slots) for birth place/date ──
    try:
        from jhora.ai.analysis import choghadiya_snapshot, _chart_tz_offset
        from jhora.calc.choghadiya import choghadiya_day
        tz = _chart_tz_offset(cd.timezone)
        chogh = choghadiya_day(cd.birth_date, cd.latitude, cd.longitude, tz)
        current = None
        now = datetime.now()
        cur = chogh.current_slot(now)
        if cur is not None:
            remaining = int((cur.end - now).total_seconds() / 60.0)
            current = {"slot": cur.name, "rating": cur.rating,
                       "lord": cur.lord.name, "is_night": cur.is_night,
                       "start": cur.start.strftime("%H:%M"),
                       "end": cur.end.strftime("%H:%M"),
                       "minutes_remaining": remaining}
        result["choghadiya"] = {
            "date": chogh.date.strftime("%Y-%m-%d"),
            "text": choghadiya_snapshot(cd),
            "day": [{"slot": s.name, "rating": s.rating, "lord": s.lord.name,
                     "start": s.start.strftime("%H:%M"), "end": s.end.strftime("%H:%M")}
                    for s in chogh.day_slots],
            "night": [{"slot": s.name, "rating": s.rating, "lord": s.lord.name,
                       "start": s.start.strftime("%H:%M"), "end": s.end.strftime("%H:%M")}
                      for s in chogh.night_slots],
            "current": current,
        }
    except Exception:
        result["choghadiya"] = {}

    # ── Muhurta adjuncts (daily windows/grades) for birth place/date ──
    try:
        from jhora.ai.analysis import _chart_tz_offset
        from jhora.calc.muhurta import Tara, compute_adjuncts, _datetime_to_jd
        muhurta_tz = _chart_tz_offset(cd.timezone)
        try:
            native_janma, _pada = Nakshatra.from_longitude(cd.moon.longitude)
        except Exception:
            native_janma = None
        adjuncts = compute_adjuncts(cd.birth_date, cd.latitude, cd.longitude,
                                    muhurta_tz, native_janma)
        day_start = _datetime_to_jd(cd.birth_date.replace(hour=0, minute=0, second=0,
                                                          microsecond=0), muhurta_tz)

        def _adjunct_hhmm(jd_value: float) -> str:
            total = int(round((((jd_value - day_start) * 24.0) % 24.0) * 60.0)) % (24 * 60)
            return f"{total // 60:02d}:{total % 60:02d}"

        if adjuncts.tara_bala is None:
            tara_json = {"name": None, "class": "unavailable", "auspicious": False}
        elif adjuncts.tara_bala is Tara.JANMA:
            tara_json = {"name": adjuncts.tara_bala.value, "class": "neutral",
                         "auspicious": False}
        else:
            tara_json = {"name": adjuncts.tara_bala.value,
                         "class": "auspicious" if adjuncts.tara_auspicious else "inauspicious",
                         "auspicious": bool(adjuncts.tara_auspicious)}
        result["muhurta_adjuncts"] = {
            "date": cd.birth_date.strftime("%Y-%m-%d"),
            "durmuhurta": [{"start": _adjunct_hhmm(w.start), "end": _adjunct_hhmm(w.end)}
                           for w in adjuncts.durmuhurta],
            "varjya": [{"start": _adjunct_hhmm(w.start), "end": _adjunct_hhmm(w.end)}
                       for w in adjuncts.varjya],
            "panchaka": [{"start": _adjunct_hhmm(w.start), "end": _adjunct_hhmm(w.end),
                          "category": w.kind}
                         for w in adjuncts.panchaka],
            "chandra_bala": adjuncts.chandra_bala.value,
            "tara_bala": tara_json,
        }
    except Exception:
        result["muhurta_adjuncts"] = {}

    return result
