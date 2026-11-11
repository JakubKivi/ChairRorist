"""System tray icon for ChairRorist."""
import threading
import time

from PIL import Image
from pystray import Icon, Menu, MenuItem

from . import logging_setup, paths, utils

logger = logging_setup.get_logger()

_MUTE_LABEL = "Mute"
_UNMUTE_LABEL = "Unmute"
_REFRESH_INTERVAL = 1.0  # seconds
_MENU_REFRESH_INTERVAL = 5.0  # seconds
_DISCONNECTED_TITLE = "Disconnected - select port"


class TrayController:
    """Owns the system-tray icon and keeps its appearance in sync with state."""

    def __init__(
        self,
        status,
        on_reset,
        on_show_warning,
        on_exit,
        on_about=None,
        on_select_port=None,
        available_ports=None,
        current_port=None,
    ):
        self._status = status
        self._on_reset = on_reset
        self._on_show_warning = on_show_warning
        self._on_exit = on_exit
        self._on_about = on_about
        self._on_select_port = on_select_port
        self._available_ports = available_ports or (list)
        self._current_port = current_port or (lambda: None)

        self._icon = None
        self._stop_event = threading.Event()

    # ---- lifecycle ------------------------------------------------------
    def run(self) -> None:
        self._icon = Icon(
            "ChairRorist",
            Image.open(paths.get_image_path("sitting.ico")),
            menu=self._build_menu(),
        )
        threading.Thread(
            target=self._update_loop, name="tray-update", daemon=True
        ).start()
        self._icon.run()

    def _build_menu(self) -> Menu:
        items = [
            MenuItem(self._ignored_text, None, enabled=False),
            MenuItem(self._respected_text, None, enabled=False),
            Menu.SEPARATOR,
        ]

        if self._on_select_port is not None:
            items.append(self._port_menu())
            items.append(Menu.SEPARATOR)

        if self._on_about is not None:
            items.append(MenuItem("About", self._about))

        items.append(MenuItem(self._mute_text, self._toggle_mute))
        if not paths.is_frozen():  # "Show Warning" is a development/testing helper
            items.append(MenuItem("Show Warning", self._show_warning))
        items.append(MenuItem("Reset", self._reset))
        items.append(MenuItem("Exit", self._exit))

        return Menu(*items)

    # ---- port submenu ---------------------------------------------------
    def _port_menu(self) -> MenuItem:
        current = self._current_port()
        try:
            available = self._available_ports()
        except (OSError, ImportError) as exc:
            logger.warning("Could not enumerate serial ports: %s", exc)
            available = []

        ports = sorted(set(available) | ({current} if current else set()))

        if not ports:
            return MenuItem(
                "Port", Menu(MenuItem("No ports found", None, enabled=False))
            )

        return MenuItem(
            "Port", Menu(*[self._make_port_item(port) for port in ports])
        )

    def _make_port_item(self, port):
        def action(icon, item):
            self._on_select_port(port)

        def checked(item):
            return port == self._current_port()

        return MenuItem(port, action, checked=checked, radio=True)

    # ---- menu text (dynamic) -------------------------------------------
    def _ignored_text(self, item) -> str:
        return f"Ignored: {self._status.ignored_notifications}"

    def _respected_text(self, item) -> str:
        return f"Respected: {self._status.realised_notifications}"

    def _mute_text(self, item) -> str:
        return _UNMUTE_LABEL if self._status.muted else _MUTE_LABEL

    # ---- menu actions ---------------------------------------------------
    def _toggle_mute(self, icon, item) -> None:
        self._status.set_muted(not self._status.muted)

    def _about(self, icon, item) -> None:
        self._on_about()

    def _show_warning(self, icon, item) -> None:
        self._on_show_warning()

    def _reset(self, icon, item) -> None:
        self._on_reset()

    def _exit(self, icon, item) -> None:
        self._on_exit()
        self._stop_event.set()
        if self._icon is not None:
            self._icon.stop()

    # ---- refresh loop ---------------------------------------------------
    def _update_loop(self) -> None:
        last_menu_refresh = 0.0
        while not self._stop_event.is_set():
            if self._status.connected:
                self._update_icon()
                self._update_title()
            else:
                self._icon.title = _DISCONNECTED_TITLE

            now = time.monotonic()
            if now - last_menu_refresh >= _MENU_REFRESH_INTERVAL:
                self._icon.menu = self._build_menu()
                last_menu_refresh = now

            self._icon.update_menu()
            self._stop_event.wait(_REFRESH_INTERVAL)

    def _update_icon(self) -> None:
        name = utils.icon_name(self._status.sitting_time, self._status.alert_interval)
        try:
            self._icon.icon = Image.open(paths.get_image_path(name))
        except (OSError, ValueError) as exc:
            logger.error("Failed to load icon %s: %s", name, exc)

    def _update_title(self) -> None:
        if self._status.sitting_time > 0:
            self._icon.title = f"Sitting time: {self._status.sitting_time_formatted}"
        else:
            self._icon.title = "You are standing!"
