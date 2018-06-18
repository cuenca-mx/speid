import json

from flask import request

from stpmex_handler import app, db
from stpmex_handler.models import OrdenEvent, Request
from stpmex_handler.tables.types import HttpRequestMethod


@app.route('/')
def health_check():
    return "I'm healthy!"


@app.route('/orden_events', methods=['POST'])
def callback_handler():
    orden = OrdenEvent.transform(request.json)
    db.session.add(orden)
    db.session.commit()
    return 'got it!'


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
