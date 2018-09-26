import datetime
import json
import os
import threading
from ast import literal_eval

import pika

from stpmex.types import Institucion
from speid import db
from speid.models import Transaction, Event
from speid.rabbit.base import (
    ConfirmModeClient, NEW_ORDER_QUEUE, RPC_QUEUE)


def callback(ch, method, _, body):
    print("Received: \n %r" % str(body))
    print("Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)
    body = body.decode()
    order = literal_eval(body)
    assert order["id"] == '251189'


def on_request(ch, method, props, body):
    print("Received RCP: \n %r" % str(body))
    response = "Ok"
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(
                         correlation_id=props.correlation_id),
                     body=str(response))
    ch.basic_ack(delivery_tag=method.delivery_tag)


class ConsumerThread(threading.Thread):
    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=os.getenv('AMPQ_ADDRESS')))
        channel = connection.channel()
        channel.queue_declare(queue=RPC_QUEUE)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(on_request, queue=RPC_QUEUE)

        print("Waiting for the message...")

        def stop():
            channel.stop_consuming()

        connection.add_timeout(10, stop)
        channel.start_consuming()
        connection.close()


class TestStpWeb:

    def test_ping(self, app):
        res = app.get('/')
        assert res.status_code == 200

    def test_generate_order(self, app):
        order = dict(
            fecha_operacion=datetime.date.today(),
            institucion_ordenante=Institucion.STP.value,
            institucion_beneficiaria=Institucion.BANORTE_IXE.value,
            clave_rastreo="12340",
            monto=1.2,
            nombre_ordenante="BANCO",
            tipo_cuenta_ordenante=40,
            cuenta_ordenante="072691004495711499",
            rfc_curp_ordenante="ND",
            nombre_beneficiario="Ricardo Sánchez",
            tipo_cuenta_beneficiario=40,
            cuenta_beneficiario="646180157000000004",
            rfc_curp_beneficiario="ND",
            concepto_pago="PRUEBA",
            referencia_numerica=2423,
            empresa="TAMIZI",
            estado="estado"
        )
        trace = [[order], {}, {"callbacks": None, "errbacks": None, "chain": None, "chord": None}]
        client = ConfirmModeClient(NEW_ORDER_QUEUE)
        client.channel.basic_publish(exchange='',
                              routing_key=client.queue,
                              body=json.dumps(trace),
                              properties=pika.BasicProperties(
                                  delivery_mode=2,  # Message persistent
                                  headers={'task': 'speid.daemon.tasks.send_order',
                                           'id': 'PRUEBA'}
                              ))

    def test_create_order(self, app):
        data = dict(
            id='251189',
            Estado='LIQUIDACION',
            Detalle="0"
        )
        res = app.post('/orden_events', data=json.dumps(data),
                       content_type='application/json')
        assert res.status_code == 201

    def test_assert_receive_create_order(self):
        queue_name = 'cuenca.stp.orden_events'
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=os.getenv('AMPQ_ADDRESS')))
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
        res = app.post('/orden_events', data=json.dumps(data),
                       content_type='application/json')
        assert res.status_code == 201

    def test_create_order_event(self, app):
        thread = ConsumerThread()
        thread.start()
        data = dict(
            Clave=2456303,
            FechaOperacion=20180618,
            InstitucionOrdenante=846,
            InstitucionBeneficiaria=90646,
            ClaveRastreo="PRUEBATAMIZI1",
            Monto=100.0,
            NombreOrdenante="BANCO",
            TipoCuentaOrdenante=40,
            CuentaOrdenante="846180000500000008",
            RFCCurpOrdenante="ND",
            NombreBeneficiario="TAMIZI",
            TipoCuentaBeneficiario=40,
            CuentaBeneficiario="646180157000000004",
            RFCCurpBeneficiario="ND",
            ConceptoPago="PRUEBA",
            ReferenciaNumerica=2423,
            Empresa="TAMIZI",
            estado="estado"
        )
        res = app.post('/ordenes', data=json.dumps(data),
                       content_type='application/json')

        assert res.status_code == 201

    def test_save_transaction(self):
        transaction_request = {
            "Clave": 2456303,
            "FechaOperacion": 20180618,
            "InstitucionOrdenante": 846,
            "InstitucionBeneficiaria": 90646,
            "ClaveRastreo": "PRUEBATAMIZI1",
            "Monto": 100.0,
            "NombreOrdenante": "BANCO",
            "TipoCuentaOrdenante": 40,
            "CuentaOrdenante": "846180000500000008",
            "RFCCurpOrdenante": "ND",
            "NombreBeneficiario": "TAMIZI",
            "TipoCuentaBeneficiario": 40,
            "CuentaBeneficiario": "646180157000000004",
            "RFCCurpBeneficiario": "ND",
            "ConceptoPago": "PRUEBA",
            "ReferenciaNumerica": 2423,
            "Empresa": "TAMIZI",
            "estado": "estado"
        }
        transaction = Transaction.transform(transaction_request)
        event = Event(transaction_id=transaction.id, type='TEST', meta='TEST')
        db.session.add(transaction)
        db.session.add(event)
        db.session.commit()
        assert transaction.id is not None
        assert event.id is not None
