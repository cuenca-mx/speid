from typing import List, Optional, Tuple

import cep
import pytz
from cep.exc import MaxRequestError, CepError
from mongoengine import DoesNotExist
from requests import HTTPError
from sentry_sdk import capture_exception
from stpmex.business_days import current_cdmx_time_zone, get_next_business_day

from speid.helpers import callback_helper
from speid.models import Account, Event, Transaction
from speid.processors import stpmex_client
from speid.tasks import celery
from speid.types import Estado, EventType

CURP_LENGTH = 18
RFC_LENGTH = 13
STP_BANK_CODE = 90646
GET_RFC_TASK_MAX_RETRIES = 7  # reintentos
GET_RFC_TASK_DELAY = 4  # Segundos


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


def get_rfc_or_curp(rfc_curp: str) -> Tuple[Optional[str], Optional[str]]:
    if not rfc_curp:
        return None, None

    if len(rfc_curp) == CURP_LENGTH:
        return rfc_curp, 'curp'
    elif len(rfc_curp) == RFC_LENGTH:
        return rfc_curp, 'rfc'
    else:
        return None, None


@celery.task(bind=True, max_retries=GET_RFC_TASK_MAX_RETRIES)
def send_transaction_status(self, transaction_id: str, state: str) -> None:
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
        rfc_curp = None
        id_type = None
        try:
            stp_transaction = stpmex_client.ordenes.consulta_clave_rastreo(
                transaction.clave_rastreo, STP_BANK_CODE, operational_date
            )
        except Exception as exc:
            capture_exception(exc)
            self.retry(countdown=GET_RFC_TASK_DELAY)
        else:
            rfc_curp, id_type = get_rfc_or_curp(stp_transaction.rfcCEP)
            if not rfc_curp:
                rfc_curp, id_type = get_rfc_or_curp(
                    stp_transaction.rfcCurpBeneficiario
                )

        # Si no hay información en la respuesta de STP
        # hacemos un segundo intento consultando directamente el CEP
        if not rfc_curp:
            try:
                transferencia = cep.Transferencia.validar(
                    fecha=transaction_local_time.date(),
                    clave_rastreo=transaction.clave_rastreo,
                    emisor=str(STP_BANK_CODE),
                    receptor=transaction.institucion_beneficiaria,
                    cuenta=transaction.cuenta_beneficiario,
                    monto=stp_transaction.monto,
                )
                assert transferencia is not None
            except MaxRequestError:
                rfc_curp, id_type = None, None
            except CepError:
                self.retry(countdown=GET_RFC_TASK_DELAY)
            except AssertionError:
                rfc_curp, id_type = None, None
            else:
                rfc_curp, id_type = get_rfc_or_curp(
                    transferencia.beneficiario.rfc
                )

        # `rfc_curp` puede contener una CURP o RFC válida
        # o None si no es un dato válido
        #
        # `id_type` puede se 'curp' o rfc' o None si no es dato válido
        if id_type == 'curp':
            curp = rfc_curp
            transaction.rfc_curp_beneficiario = rfc_curp
            transaction.save()
        elif id_type == 'rfc':
            rfc = rfc_curp
            transaction.rfc_curp_beneficiario = rfc_curp
            transaction.save()
        else:
            rfc_curp = None
            curp = None
            rfc = None

        # Si no se pudo obtener el RFC o CURP de ninguna fuente se reintenta
        # en 2 segundos
        if not rfc_curp and self.request.retries < GET_RFC_TASK_MAX_RETRIES:
            self.retry(countdown=GET_RFC_TASK_DELAY)

    callback_helper.set_status_transaction(
        transaction.speid_id, state, curp, rfc
    )
