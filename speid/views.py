import json

from flask import abort, request
from mongoengine import DoesNotExist
from sentry_sdk import capture_exception
from stpmex.exc import StpmexException

from speid import app
from speid.helpers.transaction_helper import process_incoming_transaction
from speid.models import Request, Transaction
from speid.types import Estado, HttpRequestMethod
from speid.utils import get, patch, post


@app.route('/')
@app.route('/healthcheck')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def create_orden_events():
    try:
        transaction = Transaction.objects.get(stp_id=request.json['id'])

        state = Estado.get_state_from_stp(request.json['Estado'])

        if state is Estado.failed:
            assert transaction.estado is not Estado.failed

        transaction.set_state(state)

        transaction.save()
    except Exception as exc:
        capture_exception(exc)

    return "got it!"


@post('/ordenes')
def create_orden():
    return process_incoming_transaction(request.json)


@get('/transactions')
def get_orders():
    estado = request.args.get('estado', default=None, type=str)
    prefix_ordenante = request.args.get(
        'prefix_ordenante', default=None, type=str
    )
    prefix_beneficiario = request.args.get(
        'prefix_beneficiario', default=None, type=str
    )
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
        transaction = Transaction.objects.get(
            id=transaction_id, estado=Estado.created
        )
    except DoesNotExist:
        abort(401)

    try:
        transaction.create_order()
    except StpmexException as e:
        return 400, str(e)
    else:
        return 201, transaction


@patch('/transactions/<transaction_id>/reverse')
def reverse_transaction(transaction_id):
    try:
        transaction = Transaction.objects.get(
            id=transaction_id, estado=Estado.created
        )
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
