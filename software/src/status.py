import sys
import time
import utils

_sitting_time = 0
_sitting_time_formatted = ""
_polling_interval =60
_alert_interval = 3600
_last_alert_time = time.time()
_connected = False

def get_conntected():
    return _connected

def get_sitting_time():
    return _sitting_time

def get_sitting_time_formatted():
    return _sitting_time_formatted

def get_polling_interval():
    return _polling_interval

def get_alert_interval():
    return _alert_interval

def get_last_alert_time():
    return _last_alert_time

def _check_main_only():
    """Checks if function is called from z main.py"""
    caller = sys._getframe(2).f_globals.get("__file__", "")
    if not caller.endswith("main.py"):
        raise RuntimeError("Error! Changing status values outside main.py!")

def set_connected(value):
    _check_main_only()
    global _connected
    _connected = value

def set_sitting_time(value):
    _check_main_only()
    global _sitting_time
    _sitting_time = value

def set_sitting_time_formatted(value):
    _check_main_only()
    global _sitting_time_formatted
    _sitting_time_formatted = value

def set_last_alert_time(value):
    _check_main_only()
    global _last_alert_time
    _last_alert_time = value

def increment():
    """Increments status variables sitting time + formated"""
    _check_main_only()
    global _sitting_time
    _sitting_time += _polling_interval
    global _sitting_time_formatted
    _sitting_time_formatted = utils.format_time(_sitting_time)

def check():
    return time.time() - _last_alert_time >= _alert_interval

def stading():
    _check_main_only()
    global _sitting_time
    _sitting_time = 0
    global _last_alert_time
    _last_alert_time = time.time()