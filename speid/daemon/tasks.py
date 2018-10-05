from stpmex import Orden

from speid import db
from speid.models import Transaction, Event
from speid.models.exceptions import StpConnectionError
from speid.models.helpers import snake_to_camel
from speid.tables.types import State
from .celery_app import app


def retry_timeout(attempts):
    return 2 * attempts


@app.task(bind=True, max_retries=5)
def send_order(self, order_dict):
    # Create event
    event_created = Event(
        type=State.created,
        meta=str(order_dict)
    )

    try:
        # Recover orden
        order_trans = {snake_to_camel(k): v for k, v in order_dict.items()}
        order = Orden(**order_trans)
        # Save transaction
        transaction = Transaction.transform_from_order(order)
        db.session.add(transaction)
        db.session.commit()

        event_created.transaction_id = transaction.id

        # Send order to STP
        order.monto = order.monto / 100
        res = order.registra()
    except ConnectionError as exc:
        self.retry(countdown=retry_timeout(self.request.retries), exc=exc)
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
    else:
        event_complete.type = State.error

    db.session.add(event_complete)
    db.session.commit()
