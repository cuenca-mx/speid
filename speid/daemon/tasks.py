import sentry_sdk
import os
from sentry_sdk import capture_exception
from sentry_sdk.integrations.celery import CeleryIntegration
from zeep.exceptions import TransportError

from speid import db
from speid.models import Event
from speid.models import Transaction
from speid.models.exceptions import MalformedOrderException
from speid.models.transaction import TransactionFactory
from speid.helpers import callback_helper
from speid.tables.types import State, Estado
from .celery_app import app


sentry_dsn = os.getenv('SENTRY_DSN')
sentry_sdk.init(sentry_dsn,
                integrations=[CeleryIntegration()])


def retry_timeout(attempts):
    return 2 * attempts


@app.task(bind=True, max_retries=5)
def send_order(self, order_val):
    try:
        execute_task(order_val)
    except MalformedOrderException as malformed_exception:
        raise malformed_exception
    except Exception as exc:
        self.retry(countdown=retry_timeout(self.request.retries), exc=exc)


def execute_task(order_val):
    try:
        execute(order_val)
    except Exception as exc:
        capture_exception(exc)
        db.session.rollback()
        execute(order_val)
        raise exc


def execute(order_val):
    # Create event
    event_created = Event(
        type=State.created,
        meta=str(order_val)
    )
    try:
        # Get version
        version = 0
        if "version" in order_val:
            version = order_val['version']
            # Recover orden

        initial_transaction, order = (
            TransactionFactory.create_transaction(version, order_val))

        if initial_transaction.estado == Estado.error:
            if initial_transaction.speid_id is not None:
                callback_helper.set_status_transaction(
                    initial_transaction.speid_id,
                    dict(
                        estado=initial_transaction.estado.value,
                        speid_id=initial_transaction.speid_id,
                        orden_id=initial_transaction.orden_id
                    )
                )
            raise MalformedOrderException()

        transaction = None
        if version != 0:
            transaction = (
                db.session.query(Transaction).filter
                (Transaction.speid_id == order_val['speid_id'])
                .first())

        if transaction is None:
            transaction = initial_transaction

        db.session.add(transaction)
        db.session.commit()
        event_created.transaction_id = transaction.id

        # Send order to STP
        order.monto = order.monto / 100

        res = order.registra()

    finally:
        db.session.add(event_created)
        db.session.commit()

    event_complete = Event(
        transaction_id=transaction.id,
        meta=str(res)
    )
    if res is not None and res.id > 0:
        transaction.orden_id = res.id
        event_complete.type = State.completed
    else:
        event_complete.type = State.error

    db.session.add(event_complete)
    db.session.commit()
