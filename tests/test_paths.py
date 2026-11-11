"""Tests for filesystem path resolution."""

import os

from chairrorist import paths


def test_is_frozen_false_when_running_from_source():
    assert paths.is_frozen() is False


def test_resource_path_is_absolute():
    assert os.path.isabs(paths.resource_path("images", "sitting.ico"))


def test_get_image_path():
    path = paths.get_image_path("sitting.ico")
    assert path.endswith(os.path.join("images", "sitting.ico"))


def test_get_data_file_path_in_dev_mode():
    # Running from source, statistics live under repo/data/dev/ — separate from
    # the production app-data directory used by the packaged executable.
    path = paths.get_data_file_path()
    assert path.endswith(os.path.join("data", "dev", "data.chairRorist"))


def test_config_file_path_in_dev_mode():
    assert paths.config_file_path().endswith("config.json")


def test_config_file_path_when_frozen(monkeypatch):
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    assert paths.config_file_path().endswith("config.production.json")


def test_app_data_path_when_frozen(monkeypatch):
    monkeypatch.setattr(paths, "is_frozen", lambda: True)
    monkeypatch.setenv(
        "APPDATA", os.path.join("C:", "Users", "Test", "AppData", "Roaming")
    )
    path = paths.app_data_path("data.chairRorist")
    assert path.endswith(os.path.join("ChairRorist", "data.chairRorist"))


def test_get_alert_file_path():
    assert paths.get_alert_file_path().endswith(
        os.path.join("data", "allerts.chairRorist")
    )
