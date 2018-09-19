import pika
import os
import json
import threading
from ast import literal_eval
from stpmex import Orden
from stpmex.types import Institucion


def callback(ch, method, properties, body):
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
        channel.queue_declare(queue='rpc_queue')

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(on_request, queue='rpc_queue')

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

        queue = channel.queue_declare(queue=queue_name, durable=True)
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
            Empresa="TAMIZI"
        )
        res = app.post('/ordenes', data=json.dumps(data),
                       content_type='application/json')

        assert res.status_code == 201

    def test_generate_order(self, app):
        data = Orden(
            conceptoPago='Prueba',
            institucionOperante=Institucion.STP.value,
            cuentaBeneficiario='072691004495711499',
            institucionContraparte=Institucion.BANORTE_IXE.value,
            monto=1.2,
            nombreBeneficiario='Ricardo Sanchez')
        res = app.post('/generate_order', data=json.dumps(data.__dict__),
                       content_type='application/json')

        assert res.status_code == 201
