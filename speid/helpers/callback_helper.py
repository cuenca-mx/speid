import os
import json
import requests
from requests.auth import HTTPBasicAuth

CALLBACK_URL = os.getenv('CALLBACK_URL')
CALLBACK_API_KEY = os.getenv('CALLBACK_API_KEY')
CALLBACK_API_SECRET = os.getenv('CALLBACK_API_SECRET')


def send_transaction(transaction):

    body = transaction.to_dict()
    response = requests.post(CALLBACK_URL,
                             json=body,
                             auth=HTTPBasicAuth(CALLBACK_API_KEY,
                                                CALLBACK_API_SECRET))
    return json.loads(response.text)


def set_status_transaction(request_id, status):
    response = requests.post('{0}/{1}'.format(CALLBACK_URL, request_id),
                             json=status,
                             auth=HTTPBasicAuth(CALLBACK_API_KEY,
                                                CALLBACK_API_SECRET))
    return response
