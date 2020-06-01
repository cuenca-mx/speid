class OrderNotFoundException(ReferenceError):
    pass


class MalformedOrderException(ValueError):
    pass


class ResendSuccessOrderException(ValueError):
    pass
