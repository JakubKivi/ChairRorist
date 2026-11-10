"""Tests for configuration loading and merging."""

import json

from chairrorist import config


def test_default_values(tmp_path):
    cfg = config.Config(str(tmp_path / "missing.json"))
    assert cfg.get("serial.baudrate") == 9600
    assert cfg.get("serial.timeout") == 1
    assert cfg.get("intervals.polling") == 5
    assert cfg.get("intervals.alert") == 3600
    assert cfg.get("hotkeys.reset_timer") == "ctrl+shift+alt+d"
    # The serial port is managed by app-data settings, not by config.
    assert cfg.get("serial.port") is None


def test_deep_merge_partial_config(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps({"serial": {"baudrate": 115200}, "intervals": {"alert": 9999}}),
        encoding="utf-8",
    )

    cfg = config.Config(str(path))
    assert cfg.get("serial.baudrate") == 115200
    assert cfg.get("serial.timeout") == 1  # from defaults
    assert cfg.get("intervals.alert") == 9999
    assert cfg.get("intervals.polling") == 5  # from defaults


def test_defaults_are_not_mutated(tmp_path):
    """Regression: a user config must not mutate Config.DEFAULT_CONFIG."""
    cfg1 = config.Config(str(tmp_path / "a.json"))
    cfg1.set("serial.baudrate", 115200)
    cfg1.set("intervals.polling", 123)

    cfg2 = config.Config(str(tmp_path / "b.json"))
    assert cfg2.get("serial.baudrate") == 9600
    assert cfg2.get("intervals.polling") == 5
    assert config.Config.DEFAULT_CONFIG["serial"]["baudrate"] == 9600


def test_get_and_set(tmp_path):
    cfg = config.Config(str(tmp_path / "c.json"))
    cfg.set("serial.timeout", 3)
    assert cfg.get("serial.timeout") == 3
    cfg.set("a.new.nested.key", 42)
    assert cfg.get("a.new.nested.key") == 42


def test_get_nonexistent_key(tmp_path):
    cfg = config.Config(str(tmp_path / "d.json"))
    assert cfg.get("nonexistent.key") is None
    assert cfg.get("nonexistent.key", "fallback") == "fallback"


def test_save_and_reload(tmp_path):
    path = tmp_path / "config.json"
    cfg = config.Config(str(path))
    cfg.set("serial.timeout", 2)
    cfg.set("intervals.polling", 30)
    cfg.save()

    reloaded = config.Config(str(path))
    assert reloaded.get("serial.timeout") == 2
    assert reloaded.get("intervals.polling") == 30


def test_invalid_json_falls_back_to_defaults(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not valid json", encoding="utf-8")
    cfg = config.Config(str(path))
    assert cfg.get("serial.baudrate") == 9600
