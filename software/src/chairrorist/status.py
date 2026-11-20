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

While the user is *away* (screen off, sleep/hibernate) nothing is counted.
Becoming away behaves like standing up: the sitting timer is reset and a
pending reminder is resolved as "respected".

Work hours are an independent, wall-clock stopwatch the user starts and stops
from the tray.
"""
import threading
import time
from collections.abc import Callable

from . import utils


class StatusManager:
    """Holds the mutable runtime state of the application."""

    def __init__(
        self,
        polling_interval: float = 5,
        alert_interval: float = 3600,
        clock: Callable[[], float] = time.time,
    ):
        self._lock = threading.RLock()
        self._polling_interval = polling_interval
        self._alert_interval = alert_interval
        # Wall clock on purpose: work hours should keep running during sleep.
        self._clock = clock

        self._away = False
        self._work_started_at: float | None = None

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

    # ---- work hours -----------------------------------------------------
    @property
    def work_active(self) -> bool:
        with self._lock:
            return self._work_started_at is not None

    def start_work(self) -> None:
        """Start the work-hours stopwatch (no-op when already running)."""
        with self._lock:
            if self._work_started_at is None:
                self._work_started_at = self._clock()

    def stop_work(self) -> None:
        with self._lock:
            self._work_started_at = None

    def work_elapsed(self) -> float:
        """Seconds since work hours were started (0 when not running)."""
        with self._lock:
            if self._work_started_at is None:
                return 0.0
            return max(self._clock() - self._work_started_at, 0.0)

    @property
    def work_elapsed_formatted(self) -> str:
        return utils.format_clock(self.work_elapsed())

    # ---- away (screen off / sleep) -------------------------------------
    @property
    def away(self) -> bool:
        with self._lock:
            return self._away

    def set_away(self, value: bool) -> bool:
        """Mark the user as away from / back at the computer.

        Becoming away resets the sitting timer exactly like standing up does.
        Returns True when that resolved a pending reminder as "respected", so
        the caller can persist the statistics.
        """
        with self._lock:
            was_away = self._away
            self._away = value
            if value and not was_away:
                return self.mark_standing()
            return False

    # ---- behaviour ------------------------------------------------------
    def increment_sitting_time(self) -> None:
        """Add one polling interval of sitting time (ignored while away)."""
        with self._lock:
            if self._away:
                return
            self._sitting_time += self._polling_interval
            self._sitting_time_formatted = utils.format_time(int(self._sitting_time))

    def should_alert(self) -> bool:
        """Return True when another full alert interval of sitting has elapsed."""
        with self._lock:
            if self._away:
                return False
            return self._sitting_time - self._alerted_up_to >= self._alert_interval

    def mark_alerted(self) -> bool:
        """Record that a reminder was shown for the current sitting level.

        Returns True when the previous reminder was just resolved as "ignored"
        (the user kept sitting until this next reminder), so the caller can
        persist it.
        """
        with self._lock:
            if self._away:
                # The user left while the reminder was being shown; the timer
                # was already reset, so there is nothing to record.
                return False

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


