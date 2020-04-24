import os

from mongoengine import DoesNotExist, NotUniqueError
from sentry_sdk import capture_exception, capture_message

from speid.models import Transaction
from speid.models.events import Event
from speid.tasks import celery
from speid.types import Estado, EventType
from speid.validations import StpTransaction

CLABES_BLOCKED = os.getenv('CLABES_BLOCKED', '')


@celery.task(bind=True, max_retries=5)
def create_transactions(self, transactions: list):
    try:
        print(transactions)
        execute(transactions)
    except Exception as e:
        capture_exception(e)
        self.retry(countdown=600, exc=e)


def execute(transactions: list):
    for transaction in transactions:
        try:
            previous_transaction = Transaction.objects.get(
                clave_rastreo=transaction['clave_rastreo']
            )
            if previous_transaction.estado == Estado.error:
                # Not in cuenca
                previous_transaction.confirm_callback_transaction()
                previous_transaction.save()
        except DoesNotExist:
            # Not in speid
            process_incoming_transaction(transaction)


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
