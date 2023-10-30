import datetime as dt
from typing import Dict, List

import cep
import pytz
from celery.exceptions import MaxRetriesExceededError
from cep.exc import CepError, MaxRequestError
from mongoengine import DoesNotExist
from stpmex.business_days import (
    current_cdmx_time_zone,
    get_next_business_day,
    get_prior_business_day,
)
from stpmex.exc import EmptyResultsError, InvalidFutureDateError

from speid.helpers import callback_helper
from speid.helpers.transaction_helper import (
    process_incoming_transaction,
    stp_model_to_dict,
)
from speid.models import Account, Event, Transaction
from speid.models.transaction import (
    REFUNDS_PAYMENTS_TYPES,
    STP_VALID_DEPOSITS_STATUSES,
)
from speid.processors import stpmex_client
from speid.tasks import celery
from speid.types import Estado, EventType, TipoTransaccion
from speid.validations.queries import DepositStatusQuery

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
            ...
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


@celery.task
def check_deposits_status(deposit: Dict) -> None:
    req = DepositStatusQuery(**deposit)
    try:
        transaction = Transaction.objects.get(
            clave_rastreo=req.clave_rastreo,
            cuenta_beneficiario=req.cuenta_beneficiario,
            tipo=TipoTransaccion.deposito,
        )
    except DoesNotExist:
        ...
    else:
        retry_incoming_transactions.apply_async(([transaction.speid_id],))

    # Si no existe en los registros se obtiene de STP y se intenta con 3 fechas
    # operativas próximas a la fecha que el cliente nos proporcionó
    fechas_operacion = [
        get_next_business_day(req.fecha_operacion),
        get_prior_business_day(req.fecha_operacion),
        get_next_business_day(req.fecha_operacion + dt.timedelta(days=1)),
    ]

    for fecha_operacion in fechas_operacion:
        try:
            recibida = (
                stpmex_client.ordenes_v2.consulta_clave_rastreo_recibida(
                    clave_rastreo=req.clave_rastreo,
                    fecha_operacion=fecha_operacion,
                )
            )
        except (InvalidFutureDateError, EmptyResultsError):
            continue
        else:
            if (
                recibida.tipoPago in REFUNDS_PAYMENTS_TYPES
                or recibida.estado not in STP_VALID_DEPOSITS_STATUSES
            ):
                return

            stp_request = stp_model_to_dict(recibida)
            process_incoming_transaction(stp_request)
            return
