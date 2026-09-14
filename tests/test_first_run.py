"""First-run experience: bundled data, ephemeris download, one-time offer."""

import sys

import pytest


def test_packaged_samples_readable():
    from importlib import resources
    ref = resources.files("jhora") / "data" / "jhd_samples.json"
    with resources.as_file(ref) as p:
        assert p.is_file()
        import json
        assert len(json.loads(p.read_text(encoding="utf-8"))) > 0


def test_atlas_falls_back_to_package():
    from jhora.io.atlas import open_default_atlas
    import jhora.io.atlas as am
    orig = am.AtlasReader

    class _Boom:
        def __init__(self, *a, **k):
            raise RuntimeError("no db")

    am.AtlasReader = _Boom
    try:
        reader = open_default_atlas(base_dir="/tmp/definitely-not-here")
        assert isinstance(reader, am.StaticAtlasReader)
        assert reader.search("delhi", max_results=5)
    finally:
        am.AtlasReader = orig


def test_download_ephemeris_success(tmp_path, monkeypatch):
    import jhora.paths as paths

    def fake_retrieve(url, out, hook=None):
        with open(out, "wb") as f:
            f.write(b"\0" * 200_000)
        return (str(out), None)

    import urllib.request
    monkeypatch.setattr(urllib.request, "urlretrieve", fake_retrieve)
    ok, msg = paths.download_ephemeris(dest=tmp_path / "ephe")
    assert ok is True
    assert (tmp_path / "ephe" / "sepl_18.se1").is_file()


def test_download_ephemeris_failure(tmp_path, monkeypatch):
    import jhora.paths as paths
    import urllib.request

    def boom(url, out, hook=None):
        raise OSError("offline")

    monkeypatch.setattr(urllib.request, "urlretrieve", boom)
    ok, msg = paths.download_ephemeris(dest=tmp_path / "ephe")
    assert ok is False
    assert msg


def test_preferences_roundtrip():
    from jhora.core.database import get_preference, set_preference
    set_preference("test_ephe_offered", "1")
    assert get_preference("test_ephe_offered") == "1"
    assert get_preference("test_missing_xyz") == ""
    set_preference("test_ephe_offered", "")


def test_teacher_knows_downloads():
    from jhora.ai.teacher import TEACHER_SYSTEM_PROMPT
    assert "jhora download-ephe" in TEACHER_SYSTEM_PROMPT
    assert "text-embedding-nomic-embed-text-v1.5" in TEACHER_SYSTEM_PROMPT
    assert "ollama pull nomic-embed-text" in TEACHER_SYSTEM_PROMPT
    assert "books" in TEACHER_SYSTEM_PROMPT


@pytest.fixture(scope="module")
def _qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


def test_offer_once_then_silent(_qapp, monkeypatch):
    import jhora.paths as paths
    import jhora.ui.main_window as mw
    from jhora.ui.main_window import MainWindow
    monkeypatch.setattr(paths, "ephe_available", lambda: None)
    seen = {}

    class _Box:
        StandardButton = type("B", (), {"Yes": 1, "No": 0})

        @staticmethod
        def question(*a, **k):
            seen["asked"] = True
            return 0  # No

    monkeypatch.setattr(mw, "QMessageBox", _Box)
    monkeypatch.setattr(paths, "download_ephemeris",
                        lambda *a, **k: (_ for _ in ()).throw(
                            AssertionError("must not download on No")))
    from jhora.core.database import get_preference, set_preference
    set_preference("ephe_offered", "")
    window = MainWindow()
    window._maybe_offer_ephemeris()
    assert seen.get("asked") is True
    assert get_preference("ephe_offered") == "1"
    seen.clear()
    window._maybe_offer_ephemeris()
    assert seen.get("asked") is None  # second call silent
    set_preference("ephe_offered", "")


def test_ephemeris_tab_has_download(_qapp):
    from jhora.ui.main_window import MainWindow
    window = MainWindow()
    assert window.eph_dl_btn.text() == "Download Swiss files"
    assert "Swiss files" in window.eph_data_status.text()
