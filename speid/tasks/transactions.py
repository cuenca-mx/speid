from mongoengine import DoesNotExist
from sentry_sdk import capture_exception

from speid.helpers import callback_helper, transaction_helper
from speid.models import Event, Transaction
from speid.tasks import celery
from speid.types import Estado, EventType


@celery.task(bind=True, max_retries=5)
def create_incoming_transactions(self, transactions: list):
    try:
        execute_create_incoming_transactions(transactions)
    except Exception as e:
        capture_exception(e)
        self.retry(countdown=600, exc=e)


def execute_create_incoming_transactions(transactions: list):
    for transaction in transactions:
        try:
            previous_transaction = Transaction.objects.get(
                clave_rastreo=transaction['ClaveRastreo'],
                fecha_operacion=transaction['FechaOperacion'],
            )
            if previous_transaction.estado == Estado.error:
                # Not in backend
                previous_transaction.confirm_callback_transaction()
                previous_transaction.save()
        except DoesNotExist:
            # Not in speid
            transaction_helper.process_incoming_transaction(transaction)


@celery.task(bind=True)
def process_outgoing_transactions(self, transactions: list):
    for request_dic in transactions:
        try:
            transaction = Transaction.objects.get(
                speid_id=request_dic['speid_id']
            )
        except DoesNotExist:
            continue

        action = request_dic['action']
        if action == Estado.succeeded.value:
            new_estado = Estado.succeeded
            event_type = EventType.completed
        elif action == Estado.failed.value:
            new_estado = Estado.failed
            event_type = EventType.error
        else:
            raise ValueError('Invalid event type')

        if transaction.estado == new_estado:
            continue
        else:
            transaction.estado = new_estado
        transaction.set_state(transaction.estado)
        transaction.events.append(
            Event(type=event_type, metadata=str('Reversed by recon task'))
        )
        transaction.save()
