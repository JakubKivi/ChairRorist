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
    # Running from source, statistics should live under repo/data/.
    path = paths.get_data_file_path()
    assert path.endswith(os.path.join("data", "data.chairRorist"))


def test_config_file_path_in_dev_mode():
    assert paths.config_file_path().endswith("config.json")


def test_get_alert_file_path():
    assert paths.get_alert_file_path().endswith(
        os.path.join("data", "allerts.chairRorist")
    )
