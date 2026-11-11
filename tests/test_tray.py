"""Tests for the tray menu structure."""

from chairrorist import paths, tray


def _make_tray():
    return tray.TrayController(
        status=None,
        on_reset=lambda: None,
        on_show_warning=lambda: None,
        on_exit=lambda: None,
        on_about=lambda: None,
        on_select_port=lambda port: None,
        available_ports=lambda: ["COM3"],
        current_port=lambda: "COM3",
    )


def _action_funcs(menu):
    """Return the set of underlying functions bound as menu actions."""
    return {
        item._action.__func__
        for item in menu.items
        if hasattr(item._action, "__func__")
    }


def test_menu_has_about_and_show_warning_in_dev(monkeypatch):
    monkeypatch.setattr(paths, "is_frozen", lambda: False)
    funcs = _action_funcs(_make_tray()._build_menu())
    assert tray.TrayController._about in funcs
    assert tray.TrayController._show_warning in funcs


def test_menu_removes_show_warning_when_frozen(monkeypatch):
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    funcs = _action_funcs(_make_tray()._build_menu())
    assert tray.TrayController._about in funcs
    assert tray.TrayController._show_warning not in funcs
