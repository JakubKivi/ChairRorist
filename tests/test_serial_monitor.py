"""Tests for the serial sensor reader."""

import pytest
from chairrorist import serial_monitor
from chairrorist.serial_monitor import SensorReader


class FakeSerial:
    def __init__(self, responses):
        self._responses = list(responses)
        self.written = []
        self.closed = False

    def write(self, data):
        self.written.append(data)

    def readline(self):
        return self._responses.pop(0)

    def close(self):
        self.closed = True


def test_read_state_sitting():
    fake = FakeSerial([b"0\r\n"])
    reader = SensorReader(fake)
    assert reader.read_state() == 0
    assert fake.written == [b"?"]


def test_read_state_standing():
    fake = FakeSerial([b"1\n"])
    reader = SensorReader(fake)
    assert reader.read_state() == 1


def test_read_state_timeout_returns_none():
    fake = FakeSerial([b""])
    reader = SensorReader(fake)
    assert reader.read_state() is None


def test_read_state_invalid_raises():
    fake = FakeSerial([b"xyz\n"])
    reader = SensorReader(fake)
    with pytest.raises(ValueError):
        reader.read_state()


def test_read_state_out_of_range_raises():
    fake = FakeSerial([b"2\n"])
    reader = SensorReader(fake)
    with pytest.raises(ValueError):
        reader.read_state()


def test_close():
    fake = FakeSerial([])
    reader = SensorReader(fake)
    reader.close()
    assert fake.closed is True


class FakePortInfo:
    def __init__(self, device):
        self.device = device


def test_list_available_ports(monkeypatch):
    monkeypatch.setattr(
        "serial.tools.list_ports.comports",
        lambda: [FakePortInfo("COM3"), FakePortInfo("COM6")],
    )
    assert serial_monitor.list_available_ports() == ["COM3", "COM6"]
