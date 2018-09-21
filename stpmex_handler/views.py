import json
from flask import jsonify, make_response, request
from stpmex_handler.rabbit.base import RpcClient, ConfirmModeClient
from stpmex_handler import app, db
from stpmex_handler.models import Request, Transaction, Event
from stpmex_handler.tables.types import HttpRequestMethod


@app.route('/')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def create_orden_events():
    rabbit_client = ConfirmModeClient('cuenca.stp.orden_events')
    rabbit_client.call(request.json)
    return make_response(jsonify(request.json), 201)


@app.route('/ordenes', methods=['POST'])
def create_orden():
    transaction = Transaction.transform(request.json)
    event_created = Event(
        transaction_id=transaction.id,
        type='CREATE',
        meta=str(request.json)
    )
    db.session.add(transaction)
    db.session.add(event_created)
    rabbit_client = RpcClient()
    resp = rabbit_client.call(request.json)
    # TODO Pending to do something with the response
    event_received = Event(
        transaction_id=transaction.id,
        type='COMPLETE',
        meta=str(resp)
    )
    db.session.add(event_received)
    db.session.commit()
    return make_response(jsonify(request.json), 201)


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
