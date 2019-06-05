import clabe
import luhnmod10
from mongoengine import DoesNotExist
from sentry_sdk import capture_exception

from speid.exc import MalformedOrderException
from speid.models import Event, Transaction
from speid.tasks import celery
from speid.types import Estado, EventType
from speid.validations import factory


def retry_timeout(attempts):
    return 2 * attempts


@celery.task(bind=True, max_retries=5)
def send_order(self, order_val):
    try:
        execute(order_val)
    except MalformedOrderException as exc:
        capture_exception(exc)
        pass
    except Exception as exc:
        capture_exception(exc)
        self.retry(countdown=retry_timeout(self.request.retries), exc=exc)


def execute(order_val):
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
        pass

    order = transaction.get_order()
    transaction.save()

    # Send order to STP
    order.monto = order.monto / 100

    res = order.registra()

    if res is not None and res.id > 0:
        transaction.stp_id = res.id
        transaction.events.append(
            Event(type=EventType.completed, metadata=str(res))
        )
    else:
        transaction.events.append(
            Event(type=EventType.error, metadata=str(res))
        )

    transaction.save()
