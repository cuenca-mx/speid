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
    pendiente = 'PENDIENTE'
    liquidacion = 'LIQUIDACION',
    devolucion = 'DEVOLUCION'
