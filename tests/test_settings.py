"""Tests for persistent app-data settings."""

from chairrorist import paths, settings


def test_load_settings_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "app_data_path", lambda *parts: str(tmp_path / parts[0]))
    assert settings.load_settings() == {}


def test_save_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "app_data_path", lambda *parts: str(tmp_path / parts[0]))
    settings.save_settings({"port": "COM6", "other": 1})
    assert settings.load_settings() == {"port": "COM6", "other": 1}


def test_get_port_none_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "app_data_path", lambda *parts: str(tmp_path / parts[0]))
    assert settings.get_port() is None


def test_set_and_get_port(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "app_data_path", lambda *parts: str(tmp_path / parts[0]))
    settings.set_port("COM9")
    assert settings.get_port() == "COM9"


def test_set_port_preserves_other_keys(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "app_data_path", lambda *parts: str(tmp_path / parts[0]))
    settings.save_settings({"port": "COM3", "favourite": True})
    settings.set_port("COM7")
    data = settings.load_settings()
    assert data["port"] == "COM7"
    assert data["favourite"] is True


def test_load_settings_invalid_json(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    path.write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(paths, "app_data_path", lambda *parts: str(path))
    assert settings.load_settings() == {}
