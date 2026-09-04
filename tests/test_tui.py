"""TUI tests — menu wiring and method existence (interactive dialogs not invoked)."""

from jhora.tui.main import JhoraTui


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
