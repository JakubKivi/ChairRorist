def format_time(sitting_time):
    """Formating time into h/m/s"""
    hours, remainder = divmod(sitting_time, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{seconds}s"