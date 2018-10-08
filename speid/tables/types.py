from enum import Enum


class HttpRequestMethod(Enum):
    get = 'GET'
    post = 'POST'


class State(Enum):
    created = 'CREATE'  # When a transaction has been received
    completed = 'COMPLETE'  # The request was processed with no errors
    error = 'ERROR'  # Something happened when the response was obtained
    received = 'RECEIVED'  # When we get the response from a transaction made


class Estado(Enum):
    submitted = 'submitted'  # Sent to STP
    success = 'success'      # LIQUIDACION from STP
    failed = 'failed'        # DEVOLUCION from STP
    error = 'error'          # Malformed order

    @classmethod
    def get_state_from_stp(cls, stp_state):
        if stp_state == 'LIQUIDACION':
            return cls.success
        if stp_state == 'DEVOLUCION':
            return cls.failed
        return cls.error
