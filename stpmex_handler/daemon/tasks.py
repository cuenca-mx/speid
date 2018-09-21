from .celery import app
from stpmex_handler.models.helpers import snake_to_camel, save_items
from .celery import stpmex
from stpmex_handler.models import Transaction, Event


@app.task
def send_order(order_dict):
    # Save transaction
    transaction = Transaction(order_dict)
    event_created = Event(
        transaction_id=transaction.id,
        type="CREATE",
        meta=str(order_dict)
    )

    # Send order to STP
    order_dict = {snake_to_camel(k): v for k, v in order_dict.items()}
    order = stpmex.Orden(**order_dict)
    res = order.registra()

    event_complete = Event(
        transaction_id=transaction.id,
        type="COMPLETE",
        meta=str(res)
    )
    if res.id > 0:
        transaction.orden_id = res.id

    save_items([transaction, event_created, event_complete])
