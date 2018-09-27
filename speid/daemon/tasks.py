from speid import db
from speid.models import Transaction, Event
from speid.models.exceptions import StpConnectionError
from speid.models.helpers import snake_to_camel
from speid.tables.types import State
from .celery_app import app
from .celery_app import stpmex


@app.task
def send_order(order_dict):
    # Save transaction
    transaction = Transaction(**order_dict)
    db.session.add(transaction)
    db.session.commit()
    event_created = Event(
        transaction_id=transaction.id,
        type=State.created,
        meta=str(order_dict)
    )

    # Send order to STP
    order_dict = {snake_to_camel(k): v for k, v in order_dict.items()}
    try:
        order = stpmex.Orden(**order_dict)
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
    else:
        event_complete.type = State.error
        # Send the order back to the queue in case of an error
        send_order.delay(order_dict)

    db.session.add(event_complete)
    db.session.commit()
