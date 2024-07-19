from datetime import datetime


def get_current_time_utc():
    """
    Get the current time in UTC format.
    """
    return datetime.utcnow()
