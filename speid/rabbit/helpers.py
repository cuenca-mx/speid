import json

from speid.rabbit.base import ConfirmModeClient


def send_order_back(transaction, queue):
    res = dict(
        estado=transaction.estado.value,
        speid_id=transaction.speid_id,
        orden_id=transaction.orden_id
    )
    rabbit_client = ConfirmModeClient(queue)
    rabbit_client.call(json.dumps(res))
