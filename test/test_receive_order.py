import json
import os
import threading

import pika

from speid.queue.base import RPC_QUEUE
from test.custom_vcr import my_vcr


def on_request(ch, method, props, body):
    print("Received RCP: \n %r" % str(body))
    b = json.loads(body)
    b['estado'] = 'success'
    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(
                         correlation_id=props.correlation_id),
                     body=json.dumps(b))
    ch.basic_ack(delivery_tag=method.delivery_tag)


class ConsumerThread(threading.Thread):
    def run(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(
            host=os.environ['AMPQ_ADDRESS']))
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


class TestReceiveOrder:

    @my_vcr.use_cassette('test/cassettes/test_create_order.yaml')
    def test_create_order_event(self, app):
        thread = ConsumerThread()
        thread.start()
        data = dict(
            Clave=2456304,
            FechaOperacion=20180618,
            InstitucionOrdenante=40012,
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
            Empresa="TAMIZI"
        )
        res = app.post('/ordenes', data=json.dumps(data),
                       content_type='application/json')

        assert res.status_code == 201

    def test_create_order_without_ordenante(self, app):
        thread = ConsumerThread()
        thread.start()
        data = dict(
            Clave=123123233,
            FechaOperacion=20190129,
            InstitucionOrdenante=40102,
            InstitucionBeneficiaria=90646,
            ClaveRastreo='MANU-00000295251',
            Monto=1000,
            NombreOrdenante='null',
            TipoCuentaOrdenante=0,
            CuentaOrdenante='null',
            RFCCurpOrdenante='null',
            NombreBeneficiario='JESUS ADOLFO ORTEGA TURRUBIATES',
            TipoCuentaBeneficiario=40,
            CuentaBeneficiario='646180157020812599',
            RFCCurpBeneficiario='ND',
            ConceptoPago='FONDEO',
            ReferenciaNumerica=1232134,
            Empresa='TAMIZI'
        )
        res = app.post('/ordenes', data=json.dumps(data),
                       content_type='application/json')

        assert res.status_code == 201
