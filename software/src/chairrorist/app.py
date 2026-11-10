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
from . import settings
from . import status as status_module
from . import tray as tray_module

logger = logging_setup.get_logger()

_RECONNECT_BACKOFF = 3.0  # seconds
_DEFAULT_PORT = "COM3"


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

        self._lock = threading.Lock()
        self._current_port = None
        self._pending_port = None
        self._port_change_event = threading.Event()

    # ---- lifecycle ------------------------------------------------------
    def run(self) -> int:
        logging_setup.setup_logging()
        self._load_statistics()

        port = self._resolve_port()
        if not self._connect_serial(port):
            notifications.notify(
                "Error", f"Failed to connect to sensor on {port}."
            )
            return 1

        try:
            self._start_ui()
            self._sensor_loop()
        finally:
            self._close_serial()

        return 0

    # ---- wiring ---------------------------------------------------------
    def _resolve_port(self) -> str:
        """Return the active port: app-data setting, else the default."""
        return settings.get_port() or _DEFAULT_PORT

    def _connect_serial(self, port: str) -> bool:
        baudrate = self.config.get("serial.baudrate", 9600)
        timeout = self.config.get("serial.timeout", 1)

        self._close_serial()

        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=timeout)
        except Exception as exc:
            logger.error("Failed to connect to %s: %s", port, exc)
            self.serial_port = None
            self.reader = None
            return False

        logger.info("Connected to serial port %s at %s baud", port, baudrate)
        self.reader = serial_monitor.SensorReader(self.serial_port)
        with self._lock:
            self._current_port = port
        return True

    def _close_serial(self) -> None:
        if self.serial_port is not None:
            try:
                self.serial_port.close()
            except Exception:
                pass
        self.serial_port = None
        self.reader = None

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
            on_select_port=self.select_port,
            available_ports=self._list_ports,
            current_port=self._get_current_port,
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

    def _get_current_port(self):
        with self._lock:
            return self._current_port

    def _list_ports(self):
        return serial_monitor.list_available_ports()

    def select_port(self, port: str) -> None:
        """Persist the selected port and ask the main loop to reconnect."""
        if port == self._get_current_port():
            return
        settings.set_port(port)
        with self._lock:
            self._pending_port = port
        self._port_change_event.set()

    def _apply_port_change(self) -> None:
        with self._lock:
            new_port = self._pending_port
            self._pending_port = None
        self._port_change_event.clear()

        if not new_port or new_port == self._get_current_port():
            return

        logger.info("Switching serial port to %s", new_port)
        self.status.set_connected(False)
        if not self._connect_serial(new_port):
            notifications.notify(
                "Error", f"Failed to connect to sensor on {new_port}."
            )

    # ---- main loop ------------------------------------------------------
    def _sensor_loop(self) -> None:
        while not self.shutdown_event.is_set():
            if self._port_change_event.is_set():
                self._apply_port_change()
                continue

            if self.reader is None:
                self.status.set_connected(False)
                self._backoff_sleep()
                continue

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
