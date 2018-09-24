import json
from flask import jsonify, make_response, request
from speid.rabbit.base import RpcClient, ConfirmModeClient
from speid import app, db
from speid.models import Request, Transaction, Event
from speid.tables.types import HttpRequestMethod
from speid.models.helpers import save_items


@app.route('/')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def create_orden_events():
    if "id" not in request.json or int(request.json["id"]) <= 0:
        return make_response(jsonify(request.json), 400)

    request_id = request.json['id']
    res = Transaction.query.filter(Transaction.orden_id == request_id).all()
    if res is None or len(res) != 1:
        event = Event(
            transaction_id=0,
            type='ERROR',
            meta=str(request.json)
        )
    else:
        transaction = res
        event = Event(
            transaction_id=transaction.id,
            type='RECEIVE',
            meta=str(request.json)
        )
    rabbit_client = ConfirmModeClient('cuenca.stp.orden_events')
    rabbit_client.call(request.json)
    save_items([event], db)
    return make_response(jsonify(request.json), 201)


@app.route('/ordenes', methods=['POST'])
def create_orden():
    transaction = Transaction.transform(request.json)
    event_created = Event(
        transaction_id=transaction.id,
        type='CREATE',
        meta=str(request.json)
    )
    rabbit_client = RpcClient()
    resp = rabbit_client.call(request.json)
    # TODO Pending to do something with the response
    event_received = Event(
        transaction_id=transaction.id,
        type='COMPLETE',
        meta=str(resp)
    )
    save_items([transaction, event_created, event_received], db)
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
