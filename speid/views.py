import json

from flask import request, abort
from mongoengine import DoesNotExist
from sentry_sdk import capture_exception

from speid import app
from speid.models import Event, Request, Transaction
from speid.types import Estado, EventType, HttpRequestMethod
from speid.utils import get, patch, post
from speid.validations import StpTransaction


@app.route('/')
@app.route('/healthcheck')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def create_orden_events():
    try:
        transaction = Transaction.objects(
            stp_id=request.json['id'], estado=Estado.submitted
        ).first()

        state = Estado.get_state_from_stp(request.json['Estado'])
        transaction.set_state(state)

        transaction.save()
    except Exception as exc:
        capture_exception(exc)

    return "got it!"


@post('/ordenes')
def create_orden():
    transaction = Transaction()
    try:
        external_transaction = StpTransaction(**request.json)
        transaction = external_transaction.transform()

        transaction.confirm_callback_transaction()
        transaction.save()

        r = request.json
        r['estado'] = Estado.convert_to_stp_state(transaction.estado)
    except Exception as exc:
        r = dict(estado='LIQUIDACION')
        transaction.estado = Estado.error
        transaction.save()
        capture_exception(exc)
    return 201, r


@get('/transactions')
def get_orders():
    estado = request.args.get('estado', default=None, type=str)
    prefix_ordenante = request.args.get('prefix_ordenante', default=None,
                                        type=str)
    prefix_beneficiario = request.args.get('prefix_beneficiario', default=None,
                                           type=str)
    query = dict()
    if estado:
        query['estado'] = estado
    if prefix_ordenante:
        query['cuenta_ordenante__startswith'] = prefix_ordenante
    if prefix_beneficiario:
        query['cuenta_beneficiario__startswith'] = prefix_beneficiario

    transactions = Transaction.objects(**query).order_by('-created_at')
    return 200, transactions


@patch('/transactions/<transaction_id>/process')
def process_transaction(transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id,
                                              estado=Estado.submitted)
    except DoesNotExist:
        abort(401)

    order = transaction.get_order()
    transaction.save()

    order.monto = order.monto / 100

    res = order.registra()

    if res is not None and res.id > 0:
        transaction.stp_id = res.id
        transaction.events.append(
            Event(type=EventType.completed, metadata=str(res))
        )
        transaction.save()
        return 201, transaction
    else:
        transaction.events.append(
            Event(type=EventType.error, metadata=str(res))
        )
        transaction.save()
        return 400, res


@patch('/transactions/<transaction_id>/reverse')
def reverse_transaction(transaction_id):
    try:
        transaction = Transaction.objects.get(id=transaction_id,
                                              estado=Estado.submitted)
    except DoesNotExist:
        abort(401)

    transaction.set_state(Estado.failed)
    transaction.save()

    return 201, transaction


@app.before_request
def log_posts():
    if request.method != 'POST':
        return
    if request.is_json:
        body = json.dumps(request.json)
    else:
        body = request.data.decode('utf-8') or json.dumps(request.form)
    req = Request(
        method=HttpRequestMethod(request.method),
        path=request.path,
        query_string=request.query_string.decode(),
        ip_address=request.remote_addr,
        headers=dict(request.headers),
        body=body,
    )
    req.save()
