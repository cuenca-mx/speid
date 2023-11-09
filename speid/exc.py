from dataclasses import dataclass


class OrderNotFoundException(ReferenceError):
    pass


class MalformedOrderException(ValueError):
    pass


class ResendSuccessOrderException(ValueError):
    pass


class ScheduleError(Exception):
    """
    Schedule STP error from 5:55pm to 6:05pm GMT
    """

    pass


@dataclass
class TransactionNeedManualReviewError(Exception):
    """
    when a person should review the transaction status manually
    """

    speid_id: str
    error: str


class DuplicatedTransaction(Exception):
    """
    Duplicated transactions are not allowed
    """
