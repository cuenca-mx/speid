import json
import logging

from flask import request
from sentry_sdk import capture_exception
from stpmex.exc import ResultsNotFound
from stpmex.types import Estado as EstadoStp

from speid import app
from speid.helpers.callback_helper import set_status_transaction
from speid.helpers.transaction_helper import process_incoming_transaction
from speid.models import Transaction, Event
from speid.processors import stpmex_client
from speid.types import Estado, TipoTransaccion, EventType

from speid.utils import post
from mongoengine import DoesNotExist

from speid.validators import TransactionStatusRequest

logging.basicConfig(level=logging.INFO, format='SPEID: %(message)s')


@app.route('/')
@app.route('/healthcheck')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def create_orden_events():
    try:
        transaction = Transaction.objects.get(
            stp_id=request.json['id'], tipo=TipoTransaccion.retiro
        )
        state = Estado.get_state_from_stp(request.json['Estado'])
        transaction.detalle = str(request.json.get('Detalle', ''))

        if state is Estado.failed:
            assert transaction.estado is not Estado.failed

        transaction.set_state(state)

        transaction.save()
    except Exception as exc:
        capture_exception(exc)

    return "got it!"


@post('/ordenes')
def create_orden():
    response = process_incoming_transaction(request.json)
    return 201, response


@post('/transactions_status')
def transactions_status():
    req = TransactionStatusRequest(**request.json)

    try:
        transaction = Transaction.objects.get(clave_rastreo=req.clave_rastreo)
    except DoesNotExist:
        transaction = None

    if transaction and transaction.tipo is TipoTransaccion.retiro:
        if transaction.estado is Estado.error:
            assert not transaction.stp_id
            transaction.estado = Estado.failed
            set_status_transaction(transaction.speid_id, transaction.estado)
            transaction.events.append(Event(type=EventType.error, metadata=str('Reversed by User request')))
            transaction.save()
            resp = 200, transaction.to_dict()
        elif transaction.estado is Estado.submitted:
            assert transaction.stp_id
            try:
                orden = stpmex_client.ordenes_v2.consulta_clave_rastreo_enviada(
                    req.clave_rastreo, req.fecha_operacion
                )
            except ResultsNotFound:
                resp = 200, dict(message=f'No se encontró {req.clave_rastreo}')
            else:
                if


    elif transaction and transaction.tipo is TipoTransaccion.deposito:
        # Cuando existe el depósito en speid pero no está en el core
        transaction.confirm_callback_transaction()
        resp = 200, transaction.to_dict()
    else:
        try:
            orden = stpmex_client.ordenes_v2.consulta_clave_rastreo_recibida(
                req.clave_rastreo, req.fecha_operacion
            )
        except ResultsNotFound:
            resp = 200, dict(message=f'No se encontró {req.clave_rastreo}')
        else:
            assert orden.estado in [EstadoStp.confirmada, EstadoStp.traspaso_liquidado]
            deposit_request = dict(
                FechaOperacion=orden.fechaOperacion.strftime('%Y%m%d'),
                InstitucionOrdenante=orden.institucionContraparte,
                InstitucionBeneficiaria=orden.institucionOperante,
                ClaveRastreo=orden.claveRastreo,
                Monto=orden.monto,
                NombreOrdenante=orden.nombreOrdenante,
                TipoCuentaOrdenante=orden.tipoCuentaOrdenante,
                CuentaOrdenante=orden.cuentaOrdenante,
                RFCCurpOrdenante=orden.rfcCurpOrdenante,
                NombreBeneficiario=orden.nombreBeneficiario,
                TipoCuentaBeneficiario=orden.tipoCuentaBeneficiario,
                CuentaBeneficiario=orden.cuentaBeneficiario,
                RFCCurpBeneficiario=orden.rfcCurpBeneficiario,
                ConceptoPago=orden.conceptoPago,
                ReferenciaNumerica=orden.referenciaNumerica,
                Empresa=orden.empresa,
                Clave=orden.idEF,
            )
            process_incoming_transaction(deposit_request)
            transaction = Transaction.objects.get(clave_rastreo=orden.claveRastreo)
            resp = 201, transaction.to_dict()

    return resp


@app.after_request
def log_responses(response):
    data = None
    if response.data:
        data = response.data.decode()
        if response.json:
            data = json.loads(data)

    headers = [str(header) for header in response.headers]

    logging.info(f'{str(response)} {"".join(headers)} {str(data)}')
    return response


@app.before_request
def log_posts():
    if 'healthcheck' in request.path:
        return
    data = None
    if request.data:
        data = request.data.decode()
        if request.is_json:
            data = json.loads(data)
    headers = [
        str(header)
        for header in request.headers
        if 'Authorization' not in header
    ]

    logging.info(f'{str(request)} {"".join(headers)} {str(data)}')
