"""JSON-LD view of a chart summary.

A self-describing serialisation derived entirely from the existing JSON
export (:func:`jhora.ai.json_export.chart_to_json`), so the two can never
disagree. The vocabulary is deliberately small and documented inline: a
schema.org ``Person`` for the native, plus a ``jyo`` prefix for the
chart terms. Nothing here recomputes a value.

The plain JSON export is unchanged; this is an additive view.
"""

from datetime import datetime
from typing import Any, Dict

from jhora.charts.chart import ChartData

#: Context: schema.org for the person, a small jyotisha vocabulary for the rest.
CONTEXT: Dict[str, Any] = {
    "@vocab": "https://schema.org/",
    "schema": "https://schema.org/",
    "jyo": "https://openjyotish.local/vocab#",
    "name": "schema:name",
    "birthDate": "schema:birthDate",
    "birthPlace": "schema:birthPlace",
    "GeoCoordinates": "schema:GeoCoordinates",
    "latitude": "schema:latitude",
    "longitude": "schema:longitude",
    "planets": "jyo:planet",
    "houses": "jyo:house",
    "dasa": "jyo:dasa",
    "arudhas": "jyo:arudha",
    "karakas": "jyo:karaka",
    "kp": "jyo:kp",
    "sign": "jyo:sign",
    "longitudeValue": "jyo:longitude",
    "nakshatra": "jyo:nakshatra",
    "pada": "jyo:pada",
    "dignity": "jyo:dignity",
    "lord": "jyo:lord",
}


def chart_to_jsonld(cd: ChartData) -> Dict[str, Any]:
    """A JSON-LD summary derived from the plain JSON export.

    Geographic coordinates are omitted entirely (never emitted), so the
    document can be shown or logged without leaking the birth place, and the
    redaction helper need not be applied to it.
    """
    from jhora.ai.json_export import chart_to_json

    data = chart_to_json(cd)
    meta = data.get("meta", {})

    doc: Dict[str, Any] = {
        "@context": CONTEXT,
        "@type": "schema:Person",
        "@id": f"jyo:chart/{meta.get('julian_day', cd.julian_day)}",
        "name": "chart",
        "birthDate": meta.get("birth_date", ""),
    }

    place = data.get("meta", {}).get("place") or data.get("meta", {}).get("city")
    if place:
        doc["birthPlace"] = {"@type": "schema:Place", "name": place}

    doc["jyo:ayanamsa"] = meta.get("ayanamsa", cd.ayanamsa_name)

    planets = []
    for key, p in data.get("planets", {}).items():
        planets.append({
            "@type": "jyo:Planet",
            "jyo:key": key,
            "jyo:name": p.get("name", key),
            "sign": p.get("sign", ""),
            "longitudeValue": p.get("longitude"),
            "nakshatra": p.get("nakshatra", ""),
            "pada": p.get("nakshatra_pada"),
            "dignity": p.get("dignity", ""),
            "lord": p.get("lord", ""),
        })
    doc["planets"] = planets

    doc["houses"] = data.get("houses", [])
    doc["dasa"] = data.get("dasa", {})
    doc["arudhas"] = data.get("arudhas", {})
    doc["karakas"] = data.get("karakas", [])
    doc["kp"] = data.get("kp", {})

    return doc
