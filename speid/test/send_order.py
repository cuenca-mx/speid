import json
import os
from ast import literal_eval

import pika
import pytest
from celery import Celery
from stpmex.types import Institucion

from speid.models.exceptions import OrderNotFoundException


def callback(ch, method, _, body):
    print("Received: \n %r" % str(body))
    print("Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)
    body = body.decode()
    order = literal_eval(body)
    assert order["Estado"] == 'LIQUIDACION'


class TestSendOrder:

    def test_generate_order(self, app):
        order = dict(
            concepto_pago='PRUEBA',
            institucion_operante=Institucion.STP.value,
            cuenta_beneficiario='072691004495711499',
            institucion_contraparte=Institucion.BANORTE_IXE.value,
            monto=1020,
            nombre_beneficiario='Ricardo Sánchez',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND'
        )
        app = Celery('stp_client')
        app.config_from_object('speid.daemon.celeryconfig')
        app.send_task('speid.daemon.tasks.send_order',
                      kwargs={'order_dict': order})

    def test_create_order_found(self, app):
        data = dict(
            id='5623943',
            Estado='LIQUIDACION',
            Detalle="0"
        )
        res = app.post('/orden_events', data=json.dumps(data),
                       content_type='application/json')
        assert res.status_code == 200

    def test_assert_receive_create_order(self):
        queue_name = 'cuenca.stp.orden_events'
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=os.environ['AMPQ_ADDRESS']))
        channel = connection.channel()

        channel.queue_declare(queue=queue_name, durable=True)
        print('Waiting for the message....')

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(callback, queue=queue_name)

        def stop():
            channel.stop_consuming()

        connection.add_timeout(10, stop)
        channel.start_consuming()
        assert channel.queue_declare(queue=queue_name, durable=True). \
                   method.message_count == 0
        connection.close()

    def test_fail_create_order(self, app):
        data = dict(
            Estado='LIQUIDACION',
            Detalle='0'
        )
        res = app.post('/orden_events', data=json.dumps(data),
                       content_type='application/json')
        assert res.status_code == 400

    def test_fail_id_create_order(self, app):
        data = dict(
            id='999999',  # An ID we don't have in the records
            Estado='LIQUIDACION',
            Detalle='0'
        )
        with pytest.raises(OrderNotFoundException):
            app.post('/orden_events', data=json.dumps(data),
                     content_type='application/json')
