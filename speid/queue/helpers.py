from speid.queue import app


def send_order_back(transaction):
    res = dict(
        estado=transaction.estado.value,
        speid_id=transaction.speid_id,
        orden_id=transaction.orden_id
    )
    app.send_task('speid.tasks', kwargs={'result': res})
