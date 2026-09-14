"""Tests for frozen-runtime paths (no PyInstaller run needed)."""

import sys


def test_not_frozen_by_default():
    from jhora.paths import is_frozen
    assert is_frozen() is False


def test_resource_path_dev():
    from jhora import paths
    p = paths.resource_path("jhcore", "ephe")
    assert str(p).endswith("jhcore/ephe")


def test_resource_path_frozen(monkeypatch):
    import jhora.paths as paths
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", "/tmp/fakebundle", raising=False)
    assert str(paths.resource_path("jhcore")) == "/tmp/fakebundle/jhcore"


def test_user_data_dir_frozen(monkeypatch, tmp_path):
    import jhora.paths as paths
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    if sys.platform == "win32":
        monkeypatch.setenv("APPDATA", str(tmp_path))
        assert str(paths.user_data_dir()).startswith(str(tmp_path))
    else:
        d = paths.user_data_dir()
        assert d.name == "OpenJyotish"


def test_default_ephe_path_dev_only():
    from jhora.paths import default_ephe_path
    assert default_ephe_path() is None


def test_tzdata_available():
    import zoneinfo
    assert zoneinfo.ZoneInfo("Europe/Rome") is not None
