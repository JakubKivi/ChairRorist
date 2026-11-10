"""ChairRorist — a system-tray assistant that reminds you to stand up.

The package is organised around small, single-responsibility modules:

- :mod:`chairrorist.config` — configuration loading (JSON with defaults)
- :mod:`chairrorist.paths` — filesystem path resolution (source vs. bundled)
- :mod:`chairrorist.settings` — persistent app-data settings (serial port)
- :mod:`chairrorist.status` — thread-safe application state
- :mod:`chairrorist.utils` — pure helper functions
- :mod:`chairrorist.logging_setup` — logging bootstrap
- :mod:`chairrorist.serial_monitor` — sensor communication
- :mod:`chairrorist.notifications` — Windows toasts & statistics persistence
- :mod:`chairrorist.tray` — system-tray icon
- :mod:`chairrorist.hotkeys` — global hotkey handling
- :mod:`chairrorist.app` — composition root / orchestration
"""

__version__ = "1.2.0"
__all__ = ["__version__"]
