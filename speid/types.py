from enum import Enum


class HttpRequestMethod(Enum):
    get = 'GET'
    post = 'POST'


class EventType(Enum):
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
        status_from_stp = dict(
            LIQUIDACION=cls.succeeded, DEVOLUCION=cls.failed
        )
        return status_from_stp.get(stp_state, cls.error)

    @classmethod
    def convert_to_stp_state(cls, status):
        status_to_stp = {
            cls.succeeded: 'LIQUIDACION',
            cls.failed: 'DEVOLUCION',
        }
        return status_to_stp.get(status, 'DEVOLUCION')
