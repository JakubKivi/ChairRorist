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


def test_run_stays_alive_on_connect_failure(monkeypatch, tmp_path):
    """A failed initial connection must not exit the app."""
    calls = []
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))

    def fake_connect(port):
        calls.append(("connect", port))
        return False

    monkeypatch.setattr(app_module.logging_setup, "setup_logging", lambda *a, **k: None)
    monkeypatch.setattr(app_module.settings, "get_port", lambda: None)
    monkeypatch.setattr(app, "_load_statistics", lambda: calls.append("stats"))
    monkeypatch.setattr(app, "_connect_serial", fake_connect)
    monkeypatch.setattr(app, "_start_ui", lambda: calls.append("ui"))
    monkeypatch.setattr(app, "_sensor_loop", lambda: calls.append("loop"))
    monkeypatch.setattr(app, "_close_serial", lambda: calls.append("close"))
    monkeypatch.setattr(
        app_module.notifications, "notify", lambda *a, **k: calls.append("notify")
    )

    assert app.run() == 0
    assert calls == ["stats", ("connect", "COM3"), "notify", "ui", "loop", "close"]


def test_run_success_path_does_not_notify(monkeypatch, tmp_path):
    calls = []
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))

    def fake_connect(port):
        calls.append(("connect", port))
        return True

    monkeypatch.setattr(app_module.logging_setup, "setup_logging", lambda *a, **k: None)
    monkeypatch.setattr(app_module.settings, "get_port", lambda: None)
    monkeypatch.setattr(app, "_load_statistics", lambda: calls.append("stats"))
    monkeypatch.setattr(app, "_connect_serial", fake_connect)
    monkeypatch.setattr(app, "_start_ui", lambda: calls.append("ui"))
    monkeypatch.setattr(app, "_sensor_loop", lambda: calls.append("loop"))
    monkeypatch.setattr(app, "_close_serial", lambda: calls.append("close"))
    monkeypatch.setattr(
        app_module.notifications, "notify", lambda *a, **k: calls.append("notify")
    )

    assert app.run() == 0
    assert calls == ["stats", ("connect", "COM3"), "ui", "loop", "close"]


def test_show_about_opens_browser(monkeypatch, tmp_path):
    opened = []
    monkeypatch.setattr(app_module.webbrowser, "open", lambda url: opened.append(url))
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))
    app._show_about()
    assert opened == [app_module.ABOUT_URL]



def test_away_change_saves_when_reminder_respected(monkeypatch, tmp_path):
    saved = []
    monkeypatch.setattr(
        app_module.notifications, "save_data", lambda i, r: saved.append((i, r))
    )
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))
    app.status._alert_pending = True  # a reminder fired and is unresolved

    app._on_away_changed(True)

    assert saved == [(0, 1)]
    assert app.status.away is True


def test_away_change_does_not_save_without_pending_reminder(monkeypatch, tmp_path):
    saved = []
    monkeypatch.setattr(
        app_module.notifications, "save_data", lambda i, r: saved.append((i, r))
    )
    app = app_module.ChairRoristApp(config=_make_config(tmp_path))

    app._on_away_changed(True)
    app._on_away_changed(False)

    assert saved == []
    assert app.status.away is False


def test_sensor_loop_counts_respected_and_ignored(monkeypatch, tmp_path):
    """End to end: sit past one reminder, stand before the next -> respected."""
    saved = []
    monkeypatch.setattr(
        app_module.notifications, "save_data", lambda i, r: saved.append((i, r))
    )
    monkeypatch.setattr(app_module.notifications, "send_warning", lambda s: None)
    config = _make_config(tmp_path)
    config.set("intervals.polling", 1)
    config.set("intervals.alert", 20)
    app = app_module.ChairRoristApp(config=config)
    monkeypatch.setattr(app.shutdown_event, "wait", lambda timeout=None: None)

    class Reader:
        def __init__(self, states):
            self.states = list(states)

        def read_state(self):
            if not self.states:
                app.shutdown_event.set()
                return 1
            return self.states.pop(0)

    # 25s sitting (reminder at 20s), then standing; then 45s sitting (the
    # 20s reminder is ignored at 40s), then standing (respects the 40s one).
    app.reader = Reader([0] * 25 + [1] + [0] * 45 + [1])
    app._sensor_loop()

    assert app.status.realised_notifications == 2
    assert app.status.ignored_notifications == 1
    assert saved[-1] == (1, 2)
