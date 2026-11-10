"""Pytest configuration for the ChairRorist test suite.

Makes the ``chairrorist`` package importable without requiring an install.
"""
import os
import sys

SRC_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "software", "src")
)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)
