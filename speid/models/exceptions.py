class StpConnectionError(ConnectionError):
    pass


class OrderNotFoundException(ReferenceError):
    pass


class MalformedOrderException(ValueError):
    pass
