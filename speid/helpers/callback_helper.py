import base64
import json
import os

import requests
from requests.auth import HTTPBasicAuth
from sentry_sdk import capture_message

CALLBACK_URL = os.environ['CALLBACK_URL']
CALLBACK_API_KEY = os.environ['CALLBACK_API_KEY']
CALLBACK_API_SECRET = os.environ['CALLBACK_API_SECRET']


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


def set_status_transaction(request_id: int, status: str):
    auth = auth_header(CALLBACK_API_KEY, CALLBACK_API_SECRET)
    response = requests.patch(
        '{0}/{1}'.format(CALLBACK_URL, request_id),
        headers=auth,
        json=dict(estado=status),
    )
    if response.status_code != 201:
        capture_message(response.text)

    return response
