import sentry_sdk
import os
from sentry_sdk import capture_exception
from sentry_sdk.integrations.celery import CeleryIntegration

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
        transaction, order = \
            TransactionFactory.create_transaction(version, order_val)

        if transaction.estado == Estado.error:
            if transaction.speid_id is not None:
                callback_helper.set_status_transaction(
                    transaction.speid_id,
                    dict(
                        estado=transaction.estado.value,
                        speid_id=transaction.speid_id,
                        orden_id=transaction.orden_id
                    )
                )
            raise MalformedOrderException()
        previous_transaction = None
        # Review if there is another transaction
        if version != 0:
            previous_transaction = (
                db.session.query(Transaction).filter
                (Transaction.speid_id == order_val['speid_id'])
                .first())
        db.session.add(transaction)
        if previous_transaction is None:
            # Save transaction
            db.session.commit()
        else:
            event_created.type = State.retry
            transaction.id = previous_transaction.id
            order.clave_rastreo = previous_transaction.clave_rastreo

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
