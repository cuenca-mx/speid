class OrderNotFoundException(ReferenceError):
    pass


class MalformedOrderException(ValueError):
    pass


class ResendSuccessOrderException(ValueError):
    pass


class ScheduleError(Exception):
    """
    Schedule STP error from 5:55pm to 6:05pm
    """

    pass
