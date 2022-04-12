from enum import Enum


class HttpRequestMethod(Enum):
    get = 'GET'
    post = 'POST'


class EventType(Enum):
    created = 'CREATE'  # When a transaction has been received
    retry = 'RETRY'  # When the transaction has been retry
    completed = 'COMPLETE'  # The request was processed with no errors
    error = 'ERROR'  # Something happened when the response was obtained
    received = 'RECEIVED'  # When we get the response from a transaction


class Estado(str, Enum):
    created = 'created'
    submitted = 'submitted'  # Sent to STP
    succeeded = 'succeeded'  # LIQUIDACION from STP
    failed = 'failed'  # DEVOLUCION from STP
    rejected = 'rejected'
    error = 'error'  # Malformed order
    deactivated = 'deactivated'

    @classmethod
    def get_state_from_stp(cls, stp_state: str) -> Enum:
        status_from_stp = dict(
            LIQUIDACION=cls.succeeded,
            DEVOLUCION=cls.failed,
            CANCELACION=cls.failed,
        )
        return status_from_stp.get(stp_state, cls.error)

    @classmethod
    def convert_to_stp_state(cls, status: Enum) -> str:
        status_to_stp = {
            cls.succeeded: 'LIQUIDACION',
            cls.failed: 'DEVOLUCION',
            cls.rejected: 'DEVOLUCION',
        }
        return status_to_stp.get(status, 'DEVOLUCION')  # type: ignore
