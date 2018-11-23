import json
import os
import requests

from flask import jsonify, make_response, request
from requests.auth import HTTPBasicAuth

from speid import app, db
from speid.models import Request, Transaction, Event
from speid.models.exceptions import OrderNotFoundException
from speid.tables.types import Estado, HttpRequestMethod, State


BE_CALLBACK_URL = os.getenv('BE_CALLBACK_URL')
CALLBACK_API_KEY = os.getenv('CALLBACK_API_KEY')
CALLBACK_API_SECRET = os.getenv('CALLBACK_API_SECRET')


@app.route('/')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def create_orden_events():
    if "id" not in request.json or int(request.json["id"]) <= 0:
        return make_response(jsonify(request.json), 400)

    request_id = request.json['id']
    transaction = db.session.query(Transaction).\
        filter_by(orden_id=request_id).one()
    if transaction is not None:

        transaction.estado = Estado.get_state_from_stp(request.json["Estado"])
        event = Event(
            transaction_id=transaction.id,
            type=State.received,
            meta=str(request.json)
        )

        requests.post('{0}/{1}'.format(BE_CALLBACK_URL, request_id),
                      dict(estado=transaction.estado.value),
                      auth=HTTPBasicAuth(CALLBACK_API_KEY,
                                         CALLBACK_API_SECRET))
        db.session.add(transaction)
        db.session.add(event)
        db.session.commit()
        return "got it!"
    raise OrderNotFoundException(f'Order Id: {request_id}')


@app.route('/ordenes', methods=['POST'])
def create_orden():
    transaction = Transaction.transform(request.json)
    db.session.add(transaction)
    db.session.commit()

    event_created = Event(
        transaction_id=transaction.id,
        type=State.created,
        meta=str(request.json)
    )
    # Consume api

    response = requests.post(BE_CALLBACK_URL,
                             transaction.__dict__,
                             auth=HTTPBasicAuth(CALLBACK_API_KEY,
                                                CALLBACK_API_SECRET))

    # Se pone en success hasta que se suba el cambio al api y
    # regrese el estado correcto
    response = {'estado': 'success'}

    event_received = Event(
        transaction_id=transaction.id,
        type=State.completed,
        meta=str(response)
    )
    db.session.add(event_created)
    db.session.add(event_received)
    db.session.commit()
    r = request.json
    r['estado'] = Estado.convert_to_stp_state(Estado(response['estado']))
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
