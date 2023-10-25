import os
from datetime import datetime, timedelta

import clabe
import luhnmod10
from mongoengine import DoesNotExist
from pydantic import ValidationError
from sentry_sdk import capture_exception
from stpmex.exc import (
    AccountDoesNotExist,
    BankCodeClabeMismatch,
    InvalidAccountType,
    InvalidAmount,
    InvalidInstitution,
    InvalidTrackingKey,
    PldRejected,
)

from speid.exc import (
    MalformedOrderException,
    ResendSuccessOrderException,
    ScheduleError,
    TransactionNeedManualReviewError,
)
from speid.helpers.task_helpers import time_in_range
from speid.models import Event, Transaction
from speid.tasks import celery
from speid.types import Estado, EventType
from speid.validations import factory

MAX_AMOUNT = int(os.getenv('MAX_AMOUNT', '9999999999999999'))
IGNORED_EXCEPTIONS = os.getenv('IGNORED_EXCEPTIONS', '').split(',')
START_DOWNTIME = datetime.strptime(
    os.getenv('START_DOWNTIME', '11:55PM'), "%I:%M%p"
).time()
STOP_DOWNTIME = datetime.strptime(
    os.getenv('STOP_DOWNTIME', '12:05AM'), "%I:%M%p"
).time()
# Tiempo en el que puede estar abajo STP en segundos
STP_COUNTDOWN = int(os.getenv('STP_COUNTDOWN', '600'))


def retry_timeout(attempts: int) -> int:
    # Los primeros 30 segundos lo intenta 5 veces
    if attempts <= 5:
        return 2 * attempts

    # Después lo intenta cada 20 minutos
    return 1200


@celery.task(bind=True, max_retries=12, name=os.environ['CELERY_TASK_NAME'])
def send_order(self, order_val: dict):
    try:
        execute(order_val)
    except (MalformedOrderException, ResendSuccessOrderException) as exc:
        capture_exception(exc)
    except ScheduleError:
        self.retry(countdown=STP_COUNTDOWN)
    except TransactionNeedManualReviewError as exc:
        capture_exception(exc)
    except Exception as exc:
        capture_exception(exc)
        self.retry(countdown=retry_timeout(self.request.retries))


def execute(order_val: dict):
    # Get version
    version = order_val.get('version', 0)
    if time_in_range(START_DOWNTIME, STOP_DOWNTIME, datetime.utcnow().time()):
        raise ScheduleError
    transaction = Transaction()
    try:
        input = factory.create(version, **order_val)
        transaction = input.transform()

        if not clabe.validate_clabe(transaction.cuenta_beneficiario) and (
            not luhnmod10.valid(transaction.cuenta_beneficiario)
        ):
            raise MalformedOrderException()
    except (MalformedOrderException, TypeError, ValueError):
        transaction.set_state(Estado.error)
        transaction.save()
        raise MalformedOrderException()

    try:
        prev_trx = Transaction.objects.get(speid_id=transaction.speid_id)
        # Si la transacción ya esta como succeeded termina
        # Puede suceder cuando se corre la misma tarea tiempo después
        # Y la transacción ya fue confirmada por stp
        assert prev_trx.estado != Estado.succeeded
        transaction = prev_trx
        transaction.events.append(Event(type=EventType.retry))
    except DoesNotExist:
        transaction.events.append(Event(type=EventType.created))
        transaction.save()
        pass
    except AssertionError:
        # Se hace un reenvío del estado de la transferencia
        # transaction.set_state(Estado.succeeded)
        # Para evitar que se vuelva a mandar o regresar se manda la excepción
        raise ResendSuccessOrderException()

    # Estas validaciones aplican para transferencias existentes que
    # pudieron haber fallado o han sido enviadas a STP
    if transaction.estado in [Estado.failed, Estado.error]:
        transaction.set_state(Estado.failed)
        return

    # Revisa el estado de una transferencia si ya tiene asignado stp_id o ha
    # pasado más de 2 hrs.
    now = datetime.utcnow()
    if transaction.stp_id or (now - transaction.created_at) > timedelta(
        hours=2
    ):
        transaction.update_stp_status()
        return

    # A partir de aquí son validaciones para transferencias nuevas
    if transaction.monto > MAX_AMOUNT:
        transaction.events.append(Event(type=EventType.error))
        transaction.save()
        raise MalformedOrderException()

    try:
        transaction.create_order()
    except (
        AccountDoesNotExist,
        BankCodeClabeMismatch,
        InvalidAccountType,
        InvalidAmount,
        InvalidInstitution,
        InvalidTrackingKey,
        PldRejected,
        ValidationError,
    ):
        transaction.set_state(Estado.failed)
        transaction.save()
