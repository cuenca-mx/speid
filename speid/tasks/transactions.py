from typing import List

import cep
import pytz
from celery.exceptions import MaxRetriesExceededError
from cep.exc import CepError, MaxRequestError
from mongoengine import DoesNotExist
from stpmex.business_days import current_cdmx_time_zone

from speid.helpers import callback_helper
from speid.models import Account, Event, Transaction
from speid.tasks import celery
from speid.types import Estado, EventType

CURP_LENGTH = 18
RFC_LENGTH = 13
STP_BANK_CODE = 90646
GET_RFC_TASK_MAX_RETRIES = 30  # reintentos
GET_RFC_TASK_DELAY = 10  # Segundos


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


@celery.task(bind=True, max_retries=GET_RFC_TASK_MAX_RETRIES)
def send_transaction_status(self, transaction_id: str, state: str) -> None:
    try:
        transaction = Transaction.objects.get(id=transaction_id)
    except DoesNotExist:
        return

    account = Account.objects.get(cuenta=transaction.cuenta_ordenante)
    rfc = None
    curp = None
    nombre_beneficiario = None

    if account.is_restricted and transaction.institucion_beneficiaria != str(
        STP_BANK_CODE
    ):
        cdmx_tz = current_cdmx_time_zone(transaction.created_at)

        created_at_utc = transaction.created_at.replace(tzinfo=pytz.utc)
        transaction_local_time = created_at_utc.astimezone(
            pytz.timezone(cdmx_tz)
        )

        rfc_curp = None

        try:
            transferencia = cep.Transferencia.validar(
                fecha=transaction_local_time.date(),
                clave_rastreo=transaction.clave_rastreo,
                emisor=str(STP_BANK_CODE),
                receptor=transaction.institucion_beneficiaria,
                cuenta=transaction.cuenta_beneficiario,
                monto=transaction.monto / 100,
            )
            assert transferencia is not None
        except MaxRequestError:
            rfc_curp = 'max retries'
        except (CepError, AssertionError):
            rfc_curp = None
        else:
            rfc_curp = str(transferencia.beneficiario.rfc)
            nombre_beneficiario = transferencia.beneficiario.nombre

            if len(rfc_curp) == CURP_LENGTH:
                curp = rfc_curp
                transaction.rfc_curp_beneficiario = rfc_curp
                transaction.save()
            elif len(rfc_curp) == RFC_LENGTH:
                rfc = rfc_curp
                transaction.rfc_curp_beneficiario = rfc_curp
                transaction.save()
            else:
                rfc_curp = None
                curp = None
                rfc = None

        # Si no se pudo obtener el RFC o CURP de ninguna fuente se reintenta
        # en 5 segundos
        if not rfc_curp or rfc_curp == 'ND':
            try:
                self.retry(countdown=GET_RFC_TASK_DELAY * self.request.retries)
            except MaxRetriesExceededError:
                ...

    callback_helper.set_status_transaction(
        transaction.speid_id, state, curp, rfc, nombre_beneficiario
    )
