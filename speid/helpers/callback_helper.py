import base64
import json
import os

import requests
from celery import Celery
from celery.result import AsyncResult
from requests.auth import HTTPBasicAuth
from requests.models import Response
from sentry_sdk import capture_message

from speid.types import Estado

BROKER = os.environ['AMPQ_ADDRESS']
CALLBACK_URL = os.environ['CALLBACK_URL']
CALLBACK_API_KEY = os.environ['CALLBACK_API_KEY']
CALLBACK_API_SECRET = os.environ['CALLBACK_API_SECRET']
# Se establece getenv por si están usando el sistema de
# callback por api no requieran configurar esto
SEND_TRANSACTION_TASK = os.getenv('SEND_TRANSACTION_TASK', '')
SEND_STATUS_TRANSACTION_TASK = os.getenv('SEND_STATUS_TRANSACTION_TASK', '')


def auth_header(username: str, password: str) -> dict:
    creds = base64.b64encode(f'{username}:{password}'.encode('ascii')).decode(
        'utf-8'
    )
    return dict(Authorization=f'Basic {creds}')


def send_transaction(transaction: dict) -> dict:
    response = requests.post(
        CALLBACK_URL,
        json=transaction,
        auth=HTTPBasicAuth(CALLBACK_API_KEY, CALLBACK_API_SECRET),
    )
    return json.loads(response.text)


def send_queue_transaction(transaction: dict) -> AsyncResult:
    queue = Celery('back_end_client', broker=BROKER)
    resp = queue.send_task(
        SEND_TRANSACTION_TASK, kwargs=dict(transaction=transaction)
    )
    return resp


def send_queue_state(speid_id: str, state: Estado) -> AsyncResult:
    queue = Celery('back_end_client', broker=BROKER)
    resp = queue.send_task(
        SEND_STATUS_TRANSACTION_TASK,
        kwargs=dict(speid_id=speid_id, state=state.value),
    )
    return resp


def set_status_transaction(request_id: int, status: str) -> Response:
    auth = auth_header(CALLBACK_API_KEY, CALLBACK_API_SECRET)
    response = requests.patch(
        '{0}/{1}'.format(CALLBACK_URL, request_id),
        headers=auth,
        json=dict(estado=status),
    )
    if response.status_code != 201:
        capture_message(response.text)

    return response
