"""Tests for install/run scripts — launchers must call real CLI commands."""

import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(name):
    with open(os.path.join(REPO, name)) as fh:
        return fh.read()


class TestLaunchers:
    def test_run_sh_uses_gui_command(self):
        text = _read("run.sh")
        assert "openjyotish gui" in text or "jhora gui" in text
        assert "--gui" not in text

    def test_run_bat_uses_gui_command(self):
        text = _read("run.bat")
        assert "openjyotish gui" in text or "jhora gui" in text
        assert "--gui" not in text

    def test_install_bat_notices(self):
        text = _read("install.bat")
        assert "run.bat" in text
        assert "openjyotish tui" in text

    def test_install_sh_notices(self):
        text = _read("install.sh")
        assert "./run.sh" in text
        assert "openjyotish tui" in text
