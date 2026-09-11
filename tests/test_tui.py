"""TUI tests — menu wiring and method existence (interactive dialogs not invoked)."""

from jhora.tui.main import JhoraTui


def _isolate_db(tmp_path, name="tui-save.db"):
    from jhora.core import database as db
    old = db._db_path
    db.set_db_path(str(tmp_path / name))
    return old


def _restore_db(old):
    from jhora.core import database as db
    db.close_all()
    db._db_path = old


def test_usl_menu_item_present():
    """User's Special Lagna is a reachable entry in the Chart menu."""
    tui = JhoraTui()
    tui.chart = object()  # bypass _check_chart guard
    from unittest import mock
    with mock.patch.object(tui, "_sub_menu") as sub:
        tui._show_chart_menu()
        items = sub.call_args[0][1]
    labels = [label for _, label, _ in items]
    assert any("User's Special Lagna" in label for label in labels)


def test_usl_action_method_exists():
    tui = JhoraTui()
    assert hasattr(tui, "_action_usl")
    assert callable(tui._action_usl)


def test_dasa_system_supported():
    """TUI dasa supports all 7 systems via _get_dasa_engine."""
    tui = JhoraTui()
    tui._dasa_seed = "moon"
    tui._dasa_sesham = "moon"
    tui._dasa_year = "solar"
    for sys in ["vimsottari", "ashtottari", "yogini", "sudasa",
                "chara", "narayana", "kalachakra"]:
        tui._dasa_system = sys
        assert tui._get_dasa_engine(sys) is not None


def test_dasa_menu_item_all_systems():
    tui = JhoraTui()
    tui.chart = object()
    from unittest import mock
    with mock.patch.object(tui, "_sub_menu") as sub:
        tui._show_dasas_menu()
        items = sub.call_args[0][1]
    labels = [label for _, label, _ in items]
    assert any("all systems" in label for label in labels)
    assert any("system/seed" in label for label in labels)


def test_save_db_stores_true_birth_time(tmp_path):
    """Charts saved from the TUI keep the birth hour, not midnight."""
    from jhora.charts.chart import ChartBuilder
    from jhora.core import database as db
    old = _isolate_db(tmp_path)
    try:
        tui = JhoraTui()
        tui.chart = ChartBuilder().build(
            2026, 7, 7, 10.5, lat=13.08, lon=80.27, tz="+0530")
        tui._action_save_db()
        conn = db.get_db()
        row = conn.execute(
            "SELECT time_hours, tz_offset, day, month, year FROM charts "
            "ORDER BY id DESC LIMIT 1").fetchone()
        assert row is not None
        assert abs(row["time_hours"] - 10.5) < 1e-6
        assert abs(row["tz_offset"] - 5.5) < 1e-9
        assert (row["day"], row["month"], row["year"]) == (7, 7, 2026)
    finally:
        _restore_db(old)
