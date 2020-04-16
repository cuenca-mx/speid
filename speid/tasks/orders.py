import datetime as dt
import os

import clabe
import luhnmod10
import newrelic.agent
from mongoengine import DoesNotExist
from sentry_sdk import capture_exception

from speid.exc import MalformedOrderException
from speid.models import Event, Transaction
from speid.tasks import celery
from speid.types import Estado, EventType
from speid.validations import factory

MAX_AMOUNT = int(os.getenv('MAX_AMOUNT', '9999999999999999'))
IGNORED_EXCEPTIONS = os.getenv('IGNORED_EXCEPTIONS', '').split(',')


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
    except MalformedOrderException as exc:
        capture_exception(exc)
        pass
    except (Exception) as exc:
        capture_exception(exc)
        self.retry(countdown=retry_timeout(self.request.retries))


def execute(order_val: dict):
    # Get version
    version = 0
    if "version" in order_val:
        version = order_val['version']

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
        transaction = prev_trx
        transaction.events.append(Event(type=EventType.retry))
    except DoesNotExist:
        transaction.events.append(Event(type=EventType.created))
        transaction.save()
        pass

    if transaction.monto > MAX_AMOUNT:
        transaction.events.append(Event(type=EventType.error))
        transaction.save()
        raise MalformedOrderException()

    if transaction.created_at > (dt.datetime.utcnow() - dt.timedelta(hours=2)):
        transaction.create_order()
    else:
        # Return transaction after 2 hours of creation
        transaction.set_state(Estado.failed)
        transaction.save()
