import sys
import time
import utils
import windowsMessage as wm

_sitting_time = 0
_sitting_time_formatted = ""
_polling_interval = 60
_alert_interval = 3600
_last_alert_time = time.time()
_connected = False

_ignored_notifications = 0
_realised_nofications = 0

_muted = False

_respected_counted_flag = False

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

def get_ignored_notifications():
    return _ignored_notifications

def set_ignored_notifications(value):
    global _ignored_notifications
    _ignored_notifications = value

def get_realised_notifications():
    return _realised_nofications

def set_realised_notifications(value):
    global _realised_notifications
    _realised_notifications = value

def get_muted():
    """Returns if the notifications are muted"""
    return _muted

def set_muted(value):
    """Sets the muted status of notifications"""
    global _muted
    _muted = value

def _check_main_only():
    """Checks if function is called from z ChairRorist.py"""
    caller = sys._getframe(2).f_globals.get("__file__", "")
    if not caller.endswith("ChairRorist.py"):
        raise RuntimeError("Error! Changing status values outside ChairRorist.py!")

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
    global _respected_counted_flag
    _respected_counted_flag = False

def check():
    return time.time() - _last_alert_time >= _alert_interval

def stading():

    global _respected_counted_flag
    global _sitting_time
    
    if not _respected_counted_flag:
        _respected_counted_flag = True

        if _sitting_time >= 3600:
            global _realised_nofications
            _realised_nofications += 1
            wm.save_data(_ignored_notifications, _realised_nofications)
    
    _check_main_only()
    _sitting_time = 0
    global _last_alert_time
    _last_alert_time = time.time()