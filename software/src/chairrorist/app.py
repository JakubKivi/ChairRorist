"""Composition root for the ChairRorist application.

This module wires the individual components together and owns the main
control loop.  It is deliberately thin: each concern lives in its own module
and is injected into the components that need it.
"""
import threading
import time

import serial

from . import config as config_module
from . import hotkeys
from . import logging_setup
from . import notifications
from . import serial_monitor
from . import status as status_module
from . import tray as tray_module

logger = logging_setup.get_logger()

_RECONNECT_BACKOFF = 3.0  # seconds


class ChairRoristApp:
    """Orchestrates serial monitoring, state, tray and hotkeys."""

    def __init__(self, config=None):
        self.config = config or config_module.load_config()
        self.status = status_module.StatusManager(
            polling_interval=self.config.get("intervals.polling", 5),
            alert_interval=self.config.get("intervals.alert", 3600),
        )
        self.serial_port = None
        self.reader = None
        self.tray = None
        self.shutdown_event = threading.Event()

    # ---- lifecycle ------------------------------------------------------
    def run(self) -> int:
        logging_setup.setup_logging()
        self._load_statistics()

        if not self._connect_serial():
            return 1

        try:
            self._start_ui()
            self._sensor_loop()
        finally:
            self._close_serial()

        return 0

    # ---- wiring ---------------------------------------------------------
    def _connect_serial(self) -> bool:
        port = self.config.get("serial.port", "COM3")
        baudrate = self.config.get("serial.baudrate", 9600)
        timeout = self.config.get("serial.timeout", 1)

        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as exc:
            logger.error("Failed to connect to %s: %s", port, exc)
            notifications.notify("Error", f"Failed to connect to sensor on {port}.")
            return False

        logger.info("Connected to serial port %s at %s baud", port, baudrate)
        self.reader = serial_monitor.SensorReader(self.serial_port)
        return True

    def _close_serial(self) -> None:
        if self.serial_port is not None:
            try:
                self.serial_port.close()
            except Exception:
                pass
            self.serial_port = None

    def _load_statistics(self) -> None:
        ignored, realised = notifications.load_data()
        self.status.set_ignored_notifications(ignored)
        self.status.set_realised_notifications(realised)

    def _start_ui(self) -> None:
        self.tray = tray_module.TrayController(
            status=self.status,
            on_reset=self._reset_timer,
            on_show_warning=self._show_warning,
            on_exit=self._exit,
        )
        threading.Thread(target=self.tray.run, name="tray", daemon=True).start()

        hotkey = self.config.get("hotkeys.reset_timer", "ctrl+shift+alt+d")
        threading.Thread(
            target=hotkeys.listen_hotkey,
            args=(hotkey, self._reset_timer),
            name="hotkey",
            daemon=True,
        ).start()

    # ---- user actions ---------------------------------------------------
    def _reset_timer(self) -> None:
        self.status.reset_timer()
        notifications.notify(
            "Timer Reset", "Sitting timer has been reset.", "images/standing.ico"
        )

    def _show_warning(self) -> None:
        notifications.send_warning(self.status)

    def _exit(self) -> None:
        self.shutdown_event.set()

    # ---- main loop ------------------------------------------------------
    def _sensor_loop(self) -> None:
        while not self.shutdown_event.is_set():
            try:
                state = self.reader.read_state()
            except ValueError as exc:
                logger.warning("%s", exc)
                self.status.set_connected(False)
                self._backoff_sleep()
                continue
            except Exception as exc:
                logger.error("Error in main loop: %s", exc)
                self.status.set_connected(False)
                self._backoff_sleep()
                continue

            if state is None:
                # Sensor did not answer within the configured timeout.
                self.status.set_connected(False)
                self._backoff_sleep()
                continue

            self.status.set_connected(True)

            if state == 0:  # sitting
                self.status.increment_sitting_time()
                if self.status.is_alert_due():
                    notifications.send_warning(self.status)
                    self.status.set_last_alert_time(time.time())
            else:  # standing
                if self.status.mark_standing():
                    notifications.save_data(
                        self.status.ignored_notifications,
                        self.status.realised_notifications,
                    )

            self.shutdown_event.wait(self.status.polling_interval)

    def _backoff_sleep(self) -> None:
        self.shutdown_event.wait(_RECONNECT_BACKOFF)


def main() -> int:
    """Entry point used by the packaged executable and ``python -m``."""
    return ChairRoristApp().run()
