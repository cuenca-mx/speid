from datetime import time


def time_in_range(start: time, end: time, now: time):
    if start <= end:
        return start <= now <= end
    return now >= start or now <= end
