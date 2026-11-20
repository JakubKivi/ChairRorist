"""Tests for the tray menu structure."""

from chairrorist import paths, status, tray


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


def _make_tray_with_status(st):
    ctrl = _make_tray()
    ctrl._status = st
    return ctrl


def test_work_toggle_label_and_elapsed_visibility():
    st = status.StatusManager(clock=lambda: 100.0)
    ctrl = _make_tray_with_status(st)

    assert ctrl._work_toggle_text(None) == "Work hours Start"
    assert ctrl._work_elapsed_visible(None) is False

    ctrl._toggle_work(None, None)
    assert st.work_active is True
    assert ctrl._work_toggle_text(None) == "Work hours Stop"
    assert ctrl._work_elapsed_visible(None) is True
    assert ctrl._work_elapsed_text(None) == "0:00:00"

    ctrl._toggle_work(None, None)
    assert st.work_active is False
    assert ctrl._work_toggle_text(None) == "Work hours Start"


def test_work_elapsed_text_shows_time_since_start():
    now = [100.0]
    st = status.StatusManager(clock=lambda: now[0])
    ctrl = _make_tray_with_status(st)
    ctrl._toggle_work(None, None)
    now[0] += 3661
    assert ctrl._work_elapsed_text(None) == "1:01:01"


def test_menu_has_work_toggle():
    funcs = _action_funcs(_make_tray()._build_menu())
    assert tray.TrayController._toggle_work in funcs


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
