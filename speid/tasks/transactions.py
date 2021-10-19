from typing import List

from mongoengine import DoesNotExist

from speid.models import Event, Transaction
from speid.tasks import celery
from speid.types import Estado, EventType


@celery.task
def retry_incoming_transactions(speid_ids: List[str]) -> None:
    for speid_id in speid_ids:
        transaction = Transaction.objects.get(speid_id=speid_id)
        transaction.confirm_callback_transaction()
        transaction.save()


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
