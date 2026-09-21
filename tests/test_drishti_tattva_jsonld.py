"""Tests for tattva dignities, the graha-drishti API and the JSON-LD view."""

import pytest

from jhora.calc.dignities import (
    DignityChecker,
    planet_tattva,
    sign_tattva,
    tattva_relation,
)
from jhora.calc.drishti import (
    ALL_GRAHAS,
    aspect_houses,
    aspects_from,
    aspects_point,
    drishti,
    receives,
)
from jhora.types.graha import Graha
from jhora.types.rasi import Rasi


class TestTattva:
    def test_planet_tattvas(self):
        assert planet_tattva(Graha.SUN) == "fire"
        assert planet_tattva(Graha.MOON) == "water"
        assert planet_tattva(Graha.MERCURY) == "earth"
        assert planet_tattva(Graha.JUPITER) == "akasha"
        assert planet_tattva(Graha.SATURN) == "air"
        assert planet_tattva(Graha.RAHU) == "air"

    def test_sign_tattvas_by_element_group(self):
        assert sign_tattva(0) == "fire"      # Aries
        assert sign_tattva(1) == "earth"     # Taurus
        assert sign_tattva(2) == "air"       # Gemini
        assert sign_tattva(3) == "water"     # Cancer
        assert sign_tattva(11) == "water"    # Pisces

    def test_sign_tattva_wraps(self):
        assert sign_tattva(12) == sign_tattva(0)

    def test_friendly_relation(self):
        assert tattva_relation("fire", "air") == "friendly"
        assert tattva_relation("earth", "water") == "friendly"
        assert tattva_relation("fire", "water") == "inimical"
        assert tattva_relation("fire", "fire") == "same"

    def test_akasha_is_friendly_to_all(self):
        for other in ("fire", "earth", "air", "water"):
            assert tattva_relation("akasha", other) == "friendly"
            assert tattva_relation(other, "akasha") == "friendly"

    def test_dignity_result_carries_tattva(self):
        checker = DignityChecker()
        r = checker.full_result(Graha.MARS, 0, 10.0)
        assert r.dignity == "moolatrikona"
        assert r.planet_tattva == "fire"
        assert r.sign_tattva == "fire"
        # state unchanged from the plain call
        assert r.dignity == checker.get_dignity(Graha.MARS, 0, 10.0)


class TestDrishtiRules:
    def test_all_planets_aspect_the_seventh(self):
        for g in ALL_GRAHAS:
            assert 7 in aspect_houses(g)

    def test_mars_special_aspects(self):
        assert aspect_houses(Graha.MARS) == (4, 7, 8)

    def test_jupiter_special_aspects(self):
        assert aspect_houses(Graha.JUPITER) == (5, 7, 9)

    def test_saturn_special_aspects(self):
        assert aspect_houses(Graha.SATURN) == (3, 7, 10)

    def test_nodes_aspect_trines(self):
        assert aspect_houses(Graha.RAHU) == (5, 7, 9)
        assert aspect_houses(Graha.KETU) == (5, 7, 9)

    def test_ordinary_planet_only_seventh(self):
        assert aspect_houses(Graha.SUN) == (7,)

    def test_aspects_from_sign(self):
        aspects = aspects_from(Graha.MARS, 0)   # Mars in Aries
        signs = {a.target_sign for a in aspects}
        assert signs == {Rasi.CANCER, Rasi.LIBRA, Rasi.SCORPIO}
        assert [a.house for a in aspects] == [4, 7, 8]


class TestDrishtiChart:
    def test_give_and_receive_are_symmetric(self, ref_chart):
        give = drishti(ref_chart)
        recv = receives(ref_chart)
        for giver, aspects in give.items():
            for a in aspects:
                for target in give:
                    if target == giver:
                        continue
                    target_sign = int(
                        ref_chart.planets[target].longitude // 30) % 12
                    if a.target_sign_index == target_sign:
                        assert giver in recv[target]

    def test_every_planet_present(self, ref_chart):
        assert set(drishti(ref_chart)) == set(ref_chart.planets)

    def test_aspects_point(self, ref_chart):
        # A planet's own sign is aspected by at least the planets in the 7th
        moon_lon = ref_chart.planets[Graha.MOON].longitude
        assert isinstance(aspects_point(ref_chart, moon_lon), list)


class TestJsonLd:
    def test_context_and_type(self, ref_chart):
        from jhora.ai.jsonld import chart_to_jsonld
        doc = chart_to_jsonld(ref_chart)
        assert doc["@type"] == "schema:Person"
        assert doc["@context"]["@vocab"] == "https://schema.org/"
        assert "jyo:" in doc["@id"]

    def test_values_agree_with_export(self, ref_chart):
        from jhora.ai.jsonld import chart_to_jsonld
        from jhora.ai.json_export import chart_to_json
        plain = chart_to_json(ref_chart)
        doc = chart_to_jsonld(ref_chart)
        assert len(doc["planets"]) == len(plain["planets"])
        for entry in doc["planets"]:
            key = entry["jyo:key"]
            assert entry["longitudeValue"] == plain["planets"][key]["longitude"]

    def test_no_coordinate_values(self, ref_chart):
        import json
        from jhora.ai.jsonld import chart_to_jsonld
        doc = chart_to_jsonld(ref_chart)
        # The @context legitimately names the terms; inspect the data only.
        data = {k: v for k, v in doc.items() if k != "@context"}
        blob = json.dumps(data)
        assert "GeoCoordinates" not in blob
        assert str(ref_chart.latitude) not in blob
        assert str(ref_chart.longitude) not in blob
        assert "geo" not in doc.get("birthPlace", {})

    def test_export_unchanged_sections(self, ref_chart):
        from jhora.ai.json_export import chart_to_json
        assert "kp" in chart_to_json(ref_chart)
