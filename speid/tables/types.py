from enum import Enum


class HttpRequestMethod(Enum):
    get = 'GET'
    post = 'POST'


class State(Enum):
    created = 'CREATE'  # When a transaction has been received
    retry = 'RETRY'   # When the transaction has been retry
    completed = 'COMPLETE'  # The request was processed with no errors
    error = 'ERROR'  # Something happened when the response was obtained
    received = 'RECEIVED'  # When we get the response from a transaction made


class Estado(Enum):
    submitted = 'submitted'  # Sent to STP
    succeeded = 'succeeded'  # LIQUIDACION from STP
    failed = 'failed'  # DEVOLUCION from STP
    error = 'error'  # Malformed order

    @classmethod
    def get_state_from_stp(cls, stp_state):
        if stp_state == 'LIQUIDACION':
            return cls.succeeded
        if stp_state == 'DEVOLUCION':
            return cls.failed
        return cls.error

    @classmethod
    def convert_to_stp_state(cls, state):
        if state == cls.succeeded:
            return 'LIQUIDACION'
        if state == cls.failed:
            return 'DEVOLUCION'
        return 'DEVOLUCION'
