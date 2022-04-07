from typing import List

from mongoengine import DoesNotExist

from speid.helpers import callback_helper
from speid.models import Account, Event, MoralAccount, Transaction
from speid.processors import stpmex_client
from speid.tasks import celery
from speid.types import Estado, EventType


@celery.task
def retry_incoming_transactions(speid_ids: List[str]) -> None:
    for speid_id in speid_ids:
        transaction = Transaction.objects.get(speid_id=speid_id)
        transaction.events.append(Event(type=EventType.retry))
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


@celery.task(bind=True, max_retries=30)
def send_transaction_status(self, transaction_id: str) -> None:
    try:
        transaction = Transaction.objects.get(id=transaction_id)
    except DoesNotExist:
        return

    account = Account.objects.get(cuenta=transaction.cuenta_ordenante)
    rfc = None
    curp = None

    if type(account) is MoralAccount and account.is_restricted:
        stp_transaction = stpmex_client.ordenes.consulta_clave_rastreo(
            transaction.clave_rastreo, 90646, transaction.created_at.date()
        )
        rfc_curp = stp_transaction.rfcCurpBeneficiario

        if not rfc_curp and self.request.retries < 30:
            #  Se intenta obtener el rfc/curp en 2 segundos
            self.retry(countdown=2)

        if rfc_curp:
            if len(rfc_curp) == 18:
                curp = rfc_curp
            elif len(rfc_curp) in [12, 13]:
                rfc = rfc_curp

            transaction.rfc_curp_beneficiario = rfc_curp
            transaction.save()

    callback_helper.set_status_transaction(
        transaction.speid_id, transaction.estado.value, curp, rfc
    )
