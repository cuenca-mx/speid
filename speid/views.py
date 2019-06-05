import json

from flask import jsonify, make_response, request
from sentry_sdk import capture_exception

from speid import app
from speid.models import Request, Transaction
from speid.types import Estado, HttpRequestMethod
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


@app.route('/ordenes', methods=['POST'])
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
    return make_response(jsonify(r), 201)


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
