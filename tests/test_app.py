"""Tests for the composition root's port handling."""

from chairrorist import app as app_module
from chairrorist import config as config_module


def _make_config(tmp_path):
    return config_module.Config(str(tmp_path / "missing.json"))


def test_resolve_port_prefers_settings(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module.settings, "get_port", lambda: "COM9")
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))
    assert app._resolve_port() == "COM9"


def test_resolve_port_falls_back_to_default(monkeypatch, tmp_path):
    monkeypatch.setattr(app_module.settings, "get_port", lambda: None)
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))
    assert app._resolve_port() == "COM3"


def test_select_port_persists_and_signals(monkeypatch, tmp_path):
    saved = []
    monkeypatch.setattr(app_module.settings, "set_port", lambda p: saved.append(p))
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))
    with app._lock:
        app._current_port = "COM3"

    app.select_port("COM6")

    assert saved == ["COM6"]
    assert app._pending_port == "COM6"
    assert app._port_change_event.is_set()


def test_select_port_same_port_is_noop(monkeypatch, tmp_path):
    saved = []
    monkeypatch.setattr(app_module.settings, "set_port", lambda p: saved.append(p))
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))
    with app._lock:
        app._current_port = "COM3"

    app.select_port("COM3")

    assert saved == []
    assert app._pending_port is None
    assert not app._port_change_event.is_set()
