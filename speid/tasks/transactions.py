from typing import List

import pytz
from mongoengine import DoesNotExist
from sentry_sdk import capture_exception
from stpmex.business_days import current_cdmx_time_zone, get_next_business_day

from speid.helpers import callback_helper
from speid.models import Account, Event, Transaction
from speid.processors import stpmex_client
from speid.tasks import celery
from speid.types import Estado, EventType

CURP_LENGTH = 18
RFC_LENGTH = 13


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

    if account.is_restricted:
        cdmx_tz = current_cdmx_time_zone(transaction.created_at)

        created_at_utc = transaction.created_at.replace(tzinfo=pytz.utc)
        transaction_local_time = created_at_utc.astimezone(
            pytz.timezone(cdmx_tz)
        )
        operational_date = get_next_business_day(transaction_local_time)

        try:
            stp_transaction = stpmex_client.ordenes.consulta_clave_rastreo(
                transaction.clave_rastreo, 90646, operational_date
            )
        except Exception as exc:
            capture_exception(exc)
            self.retry(countdown=2)

        rfc_curp = stp_transaction.rfcCurpBeneficiario

        if not rfc_curp and self.request.retries < 30:
            #  Se intenta obtener el rfc/curp en 2 segundos
            self.retry(countdown=2)

        if rfc_curp:
            if len(rfc_curp) == CURP_LENGTH:
                curp = rfc_curp
                transaction.rfc_curp_beneficiario = rfc_curp
                transaction.save()
            elif len(rfc_curp) == RFC_LENGTH:
                rfc = rfc_curp
                transaction.rfc_curp_beneficiario = rfc_curp
                transaction.save()
            else:
                ...

    callback_helper.set_status_transaction(
        transaction.speid_id, transaction.estado.value, curp, rfc
    )
