"""Tests for pure helper functions."""

from chairrorist import utils


def test_format_time_seconds():
    assert utils.format_time(0) == "0s"
    assert utils.format_time(30) == "30s"
    assert utils.format_time(59) == "59s"


def test_format_time_minutes():
    assert utils.format_time(60) == "1m"
    assert utils.format_time(90) == "1m"
    assert utils.format_time(150) == "2m"
    assert utils.format_time(3599) == "59m"


def test_format_time_hours():
    assert utils.format_time(3600) == "1h 0m"
    assert utils.format_time(3660) == "1h 1m"
    assert utils.format_time(7200) == "2h 0m"


def test_icon_name_standing():
    assert utils.icon_name(0, 3600) == "standing.ico"


def test_icon_name_sitting():
    assert utils.icon_name(1, 3600) == "sitting.ico"
    assert utils.icon_name(3600, 3600) == "sitting.ico"


def test_icon_name_exploding():
    assert utils.icon_name(3601, 3600) == "Exploding.ico"

