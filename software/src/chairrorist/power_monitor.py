"""Windows power-state monitoring (screen off, sleep and hibernate).

A hidden top-level window receives ``WM_POWERBROADCAST`` messages:

* ``PBT_APMSUSPEND`` / ``PBT_APMRESUME*`` for sleep and hibernate, and
* ``PBT_POWERSETTINGCHANGE`` for ``GUID_CONSOLE_DISPLAY_STATE`` (screen off/on).

The user is considered *away* while the display is off **or** the machine is
suspended; :class:`PowerMonitor` calls ``on_change(away)`` whenever that
combined state flips.  Only ``ctypes`` is used, so there is no extra
dependency.  The message loop runs on its own daemon thread.
"""
import ctypes
import threading
import uuid
from collections.abc import Callable
from ctypes import wintypes

from . import logging_setup

logger = logging_setup.get_logger()

WM_QUIT = 0x0012
WM_POWERBROADCAST = 0x0218

PBT_APMSUSPEND = 0x0004
PBT_APMRESUMESUSPEND = 0x0007
PBT_APMRESUMEAUTOMATIC = 0x0012
PBT_POWERSETTINGCHANGE = 0x8013

DEVICE_NOTIFY_WINDOW_HANDLE = 0x0

GUID_CONSOLE_DISPLAY_STATE = uuid.UUID("6FE69556-704A-47A0-8F24-C28D936FDA47")
_DISPLAY_OFF = 0  # 1 = on, 2 = dimmed (both count as "present")

_WINDOW_CLASS = "ChairRoristPowerMonitor"


class PowerState:
    """Pure state machine that folds power events into one *away* flag."""

    def __init__(self, on_change: Callable[[bool], None]):
        self._on_change = on_change
        self._display_off = False
        self._suspended = False
        self._away = False

    @property
    def away(self) -> bool:
        return self._away

    def handle_power_event(self, event: int) -> None:
        """Handle a ``PBT_APM*`` event code."""
        if event == PBT_APMSUSPEND:
            self._suspended = True
        elif event == PBT_APMRESUMESUSPEND:
            # The user woke the machine, so the screen is coming back on even
            # if no display notification reaches us.
            self._suspended = False
            self._display_off = False
        elif event == PBT_APMRESUMEAUTOMATIC:
            self._suspended = False
        else:
            return
        self._update()

    def handle_display_state(self, value: int) -> None:
        """Handle a ``GUID_CONSOLE_DISPLAY_STATE`` value (0 off, 1 on, 2 dim)."""
        self._display_off = value == _DISPLAY_OFF
        self._update()

    def _update(self) -> None:
        away = self._display_off or self._suspended
        if away != self._away:
            self._away = away
            self._on_change(away)


class _GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_ubyte * 8),
    ]

    @classmethod
    def from_uuid(cls, value: uuid.UUID) -> "_GUID":
        return cls.from_buffer_copy(value.bytes_le)


class _PowerBroadcastSetting(ctypes.Structure):
    _fields_ = [
        ("PowerSetting", _GUID),
        ("DataLength", wintypes.DWORD),
        ("Data", ctypes.c_ubyte * 1),
    ]


class PowerMonitor:
    """Runs a hidden window on a thread and reports away/back transitions."""

    def __init__(self, on_change: Callable[[bool], None]):
        self._state = PowerState(on_change)
        self._thread: threading.Thread | None = None
        self._thread_id: int | None = None
        self._ready = threading.Event()
        self._wndproc = None  # keep a reference so it is not garbage collected

    # ---- lifecycle ------------------------------------------------------
    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run, name="power-monitor", daemon=True
        )
        self._thread.start()
        self._ready.wait(timeout=5)

    def stop(self) -> None:
        if self._thread_id is not None:
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)

    # ---- message handling ----------------------------------------------
    def _handle_message(self, msg: int, wparam: int, lparam: int) -> None:
        if msg != WM_POWERBROADCAST:
            return
        if wparam == PBT_POWERSETTINGCHANGE and lparam:
            setting = ctypes.cast(
                lparam, ctypes.POINTER(_PowerBroadcastSetting)
            ).contents
            if bytes(setting.PowerSetting) == GUID_CONSOLE_DISPLAY_STATE.bytes_le:
                self._state.handle_display_state(setting.Data[0])
        else:
            self._state.handle_power_event(int(wparam))

    # ---- win32 plumbing -------------------------------------------------
    def _run(self) -> None:
        try:
            self._run_message_loop()
        except Exception as exc:  # noqa: BLE001 - a platform quirk must not kill the app
            logger.error("Power monitor stopped: %s", exc)
        finally:
            self._ready.set()

    def _run_message_loop(self) -> None:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        lresult = ctypes.c_ssize_t
        wndproc_type = ctypes.WINFUNCTYPE(
            lresult, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
        )

        class WNDCLASSW(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", wndproc_type),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HANDLE),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HANDLE),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        user32.DefWindowProcW.argtypes = [
            wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
        ]
        user32.DefWindowProcW.restype = lresult
        user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
        user32.RegisterClassW.restype = wintypes.ATOM
        user32.CreateWindowExW.argtypes = [
            wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
        ]
        user32.CreateWindowExW.restype = wintypes.HWND
        user32.RegisterPowerSettingNotification.argtypes = [
            wintypes.HANDLE, ctypes.POINTER(_GUID), wintypes.DWORD,
        ]
        user32.RegisterPowerSettingNotification.restype = wintypes.HANDLE
        user32.GetMessageW.argtypes = [
            ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT,
        ]
        user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        kernel32.GetModuleHandleW.restype = wintypes.HINSTANCE

        def wndproc(hwnd, msg, wparam, lparam):
            try:
                self._handle_message(msg, wparam, lparam)
            except Exception as exc:  # noqa: BLE001 - must not cross the C boundary
                logger.error("Power event handling failed: %s", exc)
            return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

        self._wndproc = wndproc_type(wndproc)
        hinstance = kernel32.GetModuleHandleW(None)

        window_class = WNDCLASSW()
        window_class.lpfnWndProc = self._wndproc
        window_class.hInstance = hinstance
        window_class.lpszClassName = _WINDOW_CLASS
        user32.RegisterClassW(ctypes.byref(window_class))

        # A regular (never shown) top-level window: message-only windows do
        # not receive the broadcast suspend/resume messages.
        hwnd = user32.CreateWindowExW(
            0, _WINDOW_CLASS, _WINDOW_CLASS, 0, 0, 0, 0, 0, None, None, hinstance, None
        )
        if not hwnd:
            raise OSError("Could not create the power-monitor window")

        guid = _GUID.from_uuid(GUID_CONSOLE_DISPLAY_STATE)
        if not user32.RegisterPowerSettingNotification(
            hwnd, ctypes.byref(guid), DEVICE_NOTIFY_WINDOW_HANDLE
        ):
            logger.warning("Screen-off notifications unavailable; sleep still tracked")

        self._thread_id = kernel32.GetCurrentThreadId()
        self._ready.set()
        logger.info("Power monitor started")

        message = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            user32.DispatchMessageW(ctypes.byref(message))

        user32.DestroyWindow(hwnd)
