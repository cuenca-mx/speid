import os
import json

from flask import jsonify, make_response, request
from sentry_sdk import capture_exception
import sentry_sdk

from speid import app, db
from speid.models import Request, Transaction, Event
from speid.tables.types import Estado, HttpRequestMethod, State
from speid.helpers import callback_helper

sentry_dsn = os.getenv('SENTRY_DSN')
sentry_sdk.init(sentry_dsn)


@app.route('/')
@app.route('/healthcheck')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def create_orden_events():

    if "id" not in request.json or int(request.json["id"]) <= 0:
        return make_response(jsonify(request.json), 400)

    try:
        request_id = request.json['id']
        transaction = (db.session.query(Transaction).
                       filter_by(orden_id=request_id).one())

        transaction.estado = Estado.get_state_from_stp(request.json["Estado"])
        event = Event(
            transaction_id=transaction.id,
            type=State.received,
            meta=str(request.json)
        )

        callback_helper.set_status_transaction(
            transaction.speid_id,
            dict(estado=transaction.estado.value))
        db.session.add(transaction)
        db.session.add(event)
        db.session.commit()
    except Exception as exc:
        capture_exception(exc)

    return "got it!"


@app.route('/ordenes', methods=['POST'])
def create_orden():
    try:
        transaction = Transaction.transform(request.json)
        db.session.add(transaction)
        db.session.commit()

        event_created = Event(
            transaction_id=transaction.id,
            type=State.created,
            meta=str(request.json)
        )
        # Consume api

        response = callback_helper.send_transaction(transaction)
        event_received = Event(
            transaction_id=transaction.id,
            type=State.completed,
            meta=str(response)
        )

        db.session.add(event_created)
        db.session.add(event_received)
        db.session.commit()
        r = request.json
        r['estado'] = Estado.convert_to_stp_state(Estado(response['status']))
    except Exception as exc:
        r = dict(estado='LIQUIDACION')
        transaction.type = State.error
        db.session.commit()
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
    path_limit = Request.__table__.c.path.type.length
    qs_limit = Request.__table__.c.query_string.type.length
    req = Request(
        method=HttpRequestMethod(request.method),
        path=request.path[:path_limit],
        query_string=request.query_string.decode()[:qs_limit],
        ip_address=request.remote_addr,
        headers=dict(request.headers),
        body=body
    )

    db.session.add(req)
    db.session.commit()
