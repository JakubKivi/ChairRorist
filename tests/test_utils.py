"""Unit tests for ChairRorist components."""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "software", "src"))

import utils
import config


class TestUtils(unittest.TestCase):
    """Test utility functions."""

    def test_format_time_seconds(self):
        """Test formatting time in seconds."""
        self.assertEqual(utils.format_time(30), "30s")

    def test_format_time_minutes(self):
        """Test formatting time in minutes."""
        self.assertEqual(utils.format_time(90), "1m")
        self.assertEqual(utils.format_time(150), "2m")

    def test_format_time_hours(self):
        """Test formatting time in hours."""
        self.assertEqual(utils.format_time(3660), "1h 1m")
        self.assertEqual(utils.format_time(7200), "2h 0m")


class TestConfig(unittest.TestCase):
    """Test configuration management."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = config.Config(":memory:")  # Use in-memory config for testing

    def test_default_values(self):
        """Test default configuration values."""
        self.assertEqual(self.config.get("serial.port"), "COM3")
        self.assertEqual(self.config.get("serial.baudrate"), 9600)
        self.assertEqual(self.config.get("intervals.polling"), 5)
        self.assertEqual(self.config.get("intervals.alert"), 3600)

    def test_get_nested_value(self):
        """Test getting nested configuration values."""
        self.assertEqual(self.config.get("serial.port"), "COM3")

    def test_set_value(self):
        """Test setting configuration values."""
        self.config.set("serial.port", "COM4")
        self.assertEqual(self.config.get("serial.port"), "COM4")

    def test_get_nonexistent_key(self):
        """Test getting non-existent key returns default."""
        self.assertIsNone(self.config.get("nonexistent.key"))
        self.assertEqual(self.config.get("nonexistent.key", "default"), "default")


if __name__ == "__main__":
    unittest.main()
