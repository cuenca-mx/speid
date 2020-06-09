import os

from mongoengine import NotUniqueError
from sentry_sdk import capture_exception, capture_message

from speid.models import Transaction
from speid.models.events import Event
from speid.types import Estado, EventType
from speid.validations import StpTransaction

CLABES_BLOCKED = os.getenv('CLABES_BLOCKED', '')
INCOMING_CLABES_BLOCKED = os.getenv('INCOMING_CLABES_BLOCKED', '')


def process_incoming_transaction(incoming_transaction):
    transaction = Transaction()
    try:
        external_transaction = StpTransaction(**incoming_transaction)
        transaction = external_transaction.transform()
        if CLABES_BLOCKED:
            clabes = CLABES_BLOCKED.split(',')
            if transaction.cuenta_beneficiario in clabes:
                capture_message('Transacción retenida')
                raise Exception
        if INCOMING_CLABES_BLOCKED:
            clabes = INCOMING_CLABES_BLOCKED.split(',')
            if transaction.cuenta_ordenante in clabes:
                capture_message('Transacción retenida por cuenta ordenante')
                raise Exception
        transaction.confirm_callback_transaction()
        transaction.save()
        r = incoming_transaction
        r['estado'] = Estado.convert_to_stp_state(transaction.estado)
    except (NotUniqueError, TypeError) as e:
        r = dict(estado='LIQUIDACION')
        capture_exception(e)
    except Exception as e:
        r = dict(estado='LIQUIDACION')
        transaction.estado = Estado.error
        transaction.events.append(Event(type=EventType.error, metadata=str(e)))
        transaction.save()
        capture_exception(e)
    return 201, r
