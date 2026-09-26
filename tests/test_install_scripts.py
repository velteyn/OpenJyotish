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

    def test_frozen_bundle_includes_glyph_fonts(self):
        fonts = os.path.join(REPO, "src", "jhora", "ui", "assets", "fonts")
        names = os.listdir(fonts)
        assert "ZodiacFontFREE.ttf" in names
        assert any(n.lower().startswith("ofl") for n in names)
        spec = _read("packaging/OpenJyotish.spec")
        assert "ui\", \"assets" in spec or 'ui/assets' in spec

    def test_windows_cli_shortcut_persists(self):
        iss = _read("packaging/windows/OpenJyotish.iss")
        assert "{cmd}" in iss and "/K" in iss
        assert "openjyotish.exe tui" in iss

    def test_release_zip_packs_ephe_downloader(self):
        yml = _read(".github/workflows/release.yml")
        assert "download_ephe.py" in yml

    def test_install_bat_echo_lines_have_no_parens(self):
        # A ')' in an echo inside an if (...) block closes the block
        # early: cmd.exe dies with ". was unexpected".
        for line in _read("install.bat").splitlines():
            s = line.strip()
            if s.lower().startswith("echo ") or s.lower() == "echo":
                assert "(" not in s and ")" not in s, s

    def test_windows_portable_zip_published(self):
        yml = _read(".github/workflows/build-binaries.yml")
        assert "Windows-portable" in yml
        # The v1.10.0 hollow-zip class: CI must assert both exes
        # are inside the portable zip and fail otherwise.
        assert "portable zip missing openjyotish.exe" in yml
        assert "portable zip missing OpenJyotish.exe" in yml

    def test_release_zip_guards_required_files(self):
        yml = _read(".github/workflows/release.yml")
        assert "missing required files" in yml
        assert "zip contents OK" in yml
