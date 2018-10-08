from speid import db
from speid.models import Event
from speid.models.exceptions import StpConnectionError, MalformedOrderException
from speid.models.transaction import TransactionFactory
from speid.rabbit import QUEUE_BACK
from speid.rabbit.helpers import send_order_back
from speid.tables.types import State, Estado
from .celery_app import app


def retry_timeout(attempts):
    return 2 * attempts


@app.task(bind=True, max_retries=5)
def send_order(self, order_val):
    try:
        execute_task(order_val)
    except ConnectionError as exc:
        self.retry(countdown=retry_timeout(self.request.retries), exc=exc)


def execute_task(order_val):
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
        # Save transaction
        db.session.add(transaction)
        db.session.commit()

        if transaction.estado == Estado.error:
            send_order_back(transaction, QUEUE_BACK)
            raise MalformedOrderException()

        event_created.transaction_id = transaction.id

        # Send order to STP
        order.monto = order.monto / 100
        res = order.registra()
    except ConnectionError:
        raise StpConnectionError(ConnectionError)
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
        send_order_back(transaction, QUEUE_BACK)
    else:
        event_complete.type = State.error

    db.session.add(event_complete)
    db.session.commit()
