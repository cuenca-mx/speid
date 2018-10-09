import json

from speid.rabbit import QUEUE_BACK
from speid.rabbit.base import ConfirmModeClient


def send_order_back(transaction):
    res = dict(
        estado=transaction.estado.value,
        speid_id=transaction.speid_id,
        orden_id=transaction.orden_id
    )
    rabbit_client = ConfirmModeClient(QUEUE_BACK)
    rabbit_client.call(json.dumps(res))
