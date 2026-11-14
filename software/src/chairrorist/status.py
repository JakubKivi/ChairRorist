"""Thread-safe application state for ChairRorist.

The :class:`StatusManager` is shared between the serial monitor thread, the
tray icon update thread and the hotkey thread.  All reads and writes are
guarded by a re-entrant lock so that no two threads can observe or mutate an
inconsistent snapshot of the state.

Sitting time is a single counter incremented by the polling interval on each
"sitting" sensor reading — never wall-clock time.  Every ``alert_interval`` of
sitting fires a reminder; that reminder is then resolved as "respected" if the
user stands up before the next reminder, or "ignored" if they are still sitting
when the next reminder fires.  Each reminder is tracked independently, so
ignoring several reminders in a row increments the ignored counter once per
reminder.
"""
import threading

from . import utils


class StatusManager:
    """Holds the mutable runtime state of the application."""

    def __init__(self, polling_interval: float = 5, alert_interval: float = 3600):
        self._lock = threading.RLock()
        self._polling_interval = polling_interval
        self._alert_interval = alert_interval

        self._connected = False
        self._sitting_time = 0
        self._sitting_time_formatted = utils.format_time(0)
        self._alerted_up_to = 0.0  # sitting-time level up to which alerts were shown
        self._alert_pending = False  # a reminder fired but wasn't resolved yet

        self._ignored_notifications = 0
        self._realised_notifications = 0
        self._muted = False

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

    # ---- notification statistics ---------------------------------------
    @property
    def ignored_notifications(self) -> int:
        with self._lock:
            return self._ignored_notifications

    def set_ignored_notifications(self, value: int) -> None:
        with self._lock:
            self._ignored_notifications = int(value)

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
        """Add one polling interval of sitting time."""
        with self._lock:
            self._sitting_time += self._polling_interval
            self._sitting_time_formatted = utils.format_time(int(self._sitting_time))

    def should_alert(self) -> bool:
        """Return True when another full alert interval of sitting has elapsed."""
        with self._lock:
            return self._sitting_time - self._alerted_up_to >= self._alert_interval

    def mark_alerted(self) -> bool:
        """Record that a reminder was shown for the current sitting level.

        Returns True when the previous reminder was just resolved as "ignored"
        (the user kept sitting until this next reminder), so the caller can
        persist it.
        """
        with self._lock:
            ignored = False
            if self._alert_pending:
                self._alert_pending = False
                self._ignored_notifications += 1
                ignored = True

            self._alerted_up_to += self._alert_interval
            self._alert_pending = True
            return ignored

    def mark_standing(self) -> bool:
        """Record a transition to standing.

        Returns True when a ``respected`` notification was newly counted, i.e.
        the user stood up after a reminder and before the next reminder.
        """
        with self._lock:
            counted = False
            if self._alert_pending:
                self._alert_pending = False
                self._realised_notifications += 1
                counted = True

            self._sitting_time = 0
            self._sitting_time_formatted = utils.format_time(0)
            self._alerted_up_to = 0.0
            return counted

    def reset_timer(self) -> None:
        """Reset the sitting timer (used by the tray menu and hotkey)."""
        with self._lock:
            self._sitting_time = 0
            self._sitting_time_formatted = utils.format_time(0)
            self._alerted_up_to = 0.0
            self._alert_pending = False


