import json

from jhora.io.atlas import AtlasReader, StaticAtlasReader, open_default_atlas


def test_static_atlas_reader_loads_sample_cities(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    sample_path = data_dir / "jhd_samples.json"
    sample_path.write_text(json.dumps([
        {
            "city": "Delhi",
            "latitude": 28.4,
            "longitude": -77.13,
            "tz_offset": -5.3,
        },
        {
            "city": "Unknown",
            "latitude": 0.0,
            "longitude": 0.0,
            "tz_offset": 0.0,
        },
        {
            "city": "Delhi",
            "latitude": 28.4,
            "longitude": -77.13,
            "tz_offset": -5.3,
        },
    ]), encoding="utf-8")

    atlas = StaticAtlasReader.from_jhd_samples(sample_path)

    results = atlas.search("del")
    assert len(results) == 1
    assert results[0].name == "Delhi"


def test_open_default_atlas_falls_back_to_sample_data(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    sample_path = data_dir / "jhd_samples.json"
    sample_path.write_text(json.dumps([
        {
            "city": "Pondicherry",
            "latitude": 9.5,
            "longitude": -78.15,
            "tz_offset": -5.3,
        },
    ]), encoding="utf-8")

    atlas = open_default_atlas(tmp_path)

    assert isinstance(atlas, StaticAtlasReader)
    assert atlas.search("pondi")[0].name == "Pondicherry"
    assert not isinstance(atlas, AtlasReader)
