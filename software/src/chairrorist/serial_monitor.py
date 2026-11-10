"""Serial sensor communication for ChairRorist."""
from typing import Optional


class SensorReader:
    """Reads the desk state (0 = sitting, 1 = standing) from the sensor.

    The Arduino only responds to a literal ``b"?"`` byte with a single
    ``0``/``1`` line, so the reader issues one query per call.
    """

    def __init__(self, serial_port):
        self._serial = serial_port

    def read_state(self) -> Optional[int]:
        """Query the sensor.

        Returns:
            0 when sitting, 1 when standing, or ``None`` when the sensor did
            not answer within the serial timeout.

        Raises:
            ValueError: when the sensor returned something that is not a valid
                ``0``/``1`` value.
        """
        self._serial.write(b"?")
        raw = self._serial.readline().strip()

        if not raw:
            return None

        try:
            value = int(raw)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid data from sensor: {raw!r}") from None

        if value not in (0, 1):
            raise ValueError(f"Invalid state received: {value}")

        return value

    def close(self) -> None:
        if self._serial is not None:
            self._serial.close()
