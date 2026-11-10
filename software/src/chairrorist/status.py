"""Thread-safe application state for ChairRorist.

The :class:`StatusManager` is shared between the serial monitor thread, the
tray icon update thread and the hotkey thread.  All reads and writes are
guarded by a re-entrant lock so that no two threads can observe or mutate an
inconsistent snapshot of the state.
"""
import threading
import time
from typing import Callable, Optional

from . import utils


class StatusManager:
    """Holds the mutable runtime state of the application."""

    def __init__(
        self,
        polling_interval: float = 5,
        alert_interval: float = 3600,
        clock: Optional[Callable[[], float]] = None,
    ):
        self._lock = threading.RLock()
        self._polling_interval = polling_interval
        self._alert_interval = alert_interval
        self._clock = clock if clock is not None else time.time

        self._connected = False
        self._sitting_time = 0
        self._sitting_time_formatted = utils.format_time(0)
        self._last_alert_time = self._clock()

        self._ignored_notifications = 0
        self._realised_notifications = 0
        self._muted = False
        self._respected_counted = False

    # ---- connection -----------------------------------------------------
    @property
    def connected(self) -> bool:
        with self._lock:
            return self._connected

    def set_connected(self, value: bool) -> None:
        with self._lock:
            self._connected = value

    # ---- sitting time ---------------------------------------------------
    @property
    def sitting_time(self) -> float:
        with self._lock:
            return self._sitting_time

    def set_sitting_time(self, value: float) -> None:
        with self._lock:
            self._sitting_time = value
            self._sitting_time_formatted = utils.format_time(int(value))

    @property
    def sitting_time_formatted(self) -> str:
        with self._lock:
            return self._sitting_time_formatted

    @property
    def polling_interval(self) -> float:
        return self._polling_interval

    @property
    def alert_interval(self) -> float:
        return self._alert_interval

    @property
    def last_alert_time(self) -> float:
        with self._lock:
            return self._last_alert_time

    def set_last_alert_time(self, value: float) -> None:
        with self._lock:
            self._last_alert_time = value

    # ---- notification statistics ---------------------------------------
    @property
    def ignored_notifications(self) -> int:
        with self._lock:
            return self._ignored_notifications

    def set_ignored_notifications(self, value: int) -> None:
        with self._lock:
            self._ignored_notifications = int(value)

    def increment_ignored_notifications(self) -> int:
        with self._lock:
            self._ignored_notifications += 1
            return self._ignored_notifications

    @property
    def realised_notifications(self) -> int:
        with self._lock:
            return self._realised_notifications

    def set_realised_notifications(self, value: int) -> None:
        with self._lock:
            self._realised_notifications = int(value)

    # ---- mute -----------------------------------------------------------
    @property
    def muted(self) -> bool:
        with self._lock:
            return self._muted

    def set_muted(self, value: bool) -> None:
        with self._lock:
            self._muted = value

    # ---- behaviour ------------------------------------------------------
    def increment_sitting_time(self) -> None:
        """Add one polling interval to the sitting time."""
        with self._lock:
            self._sitting_time += self._polling_interval
            self._sitting_time_formatted = utils.format_time(int(self._sitting_time))
            self._respected_counted = False

    def is_alert_due(self) -> bool:
        """Return True when enough time has elapsed since the last alert."""
        with self._lock:
            return self._clock() - self._last_alert_time >= self._alert_interval

    def mark_standing(self) -> bool:
        """Record a transition to standing.

        Returns True when a ``respected`` notification was newly counted,
        i.e. the user stood up after having sat through a full alert interval.
        """
        with self._lock:
            counted = False
            if not self._respected_counted:
                self._respected_counted = True
                if self._sitting_time >= self._alert_interval:
                    self._realised_notifications += 1
                    counted = True

            self._sitting_time = 0
            self._sitting_time_formatted = utils.format_time(0)
            self._last_alert_time = self._clock()
            return counted

    def reset_timer(self) -> None:
        """Reset the sitting timer (used by the tray menu and hotkey)."""
        with self._lock:
            self._sitting_time = 0
            self._sitting_time_formatted = utils.format_time(0)
            self._last_alert_time = self._clock()
