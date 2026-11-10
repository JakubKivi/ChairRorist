"""Pure, side-effect free helper functions."""


def format_time(sitting_time: int) -> str:
    """Format a number of seconds as a compact human-readable string."""
    hours, remainder = divmod(int(sitting_time), 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    if minutes > 0:
        return f"{minutes}m"
    return f"{seconds}s"


def icon_name(sitting_time: int, alert_interval: int) -> str:
    """Return the tray icon filename for the current sitting time."""
    if sitting_time <= 0:
        return "standing.ico"
    if sitting_time > alert_interval:
        return "Exploding.ico"
    return "sitting.ico"
