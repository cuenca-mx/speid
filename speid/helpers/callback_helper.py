import os
import requests
from requests.auth import HTTPBasicAuth


CALLBACK_URL = os.getenv('CALLBACK_URL')
CALLBACK_API_KEY = os.getenv('CALLBACK_API_KEY')
CALLBACK_API_SECRET = os.getenv('CALLBACK_API_SECRET')


def send_transaction(transaction):
    response = requests.post(CALLBACK_URL,
                             transaction.__dict__,
                             auth=HTTPBasicAuth(CALLBACK_API_KEY,
                                                CALLBACK_API_SECRET))

    # Se pone en success hasta que se suba el cambio al api y
    # regrese el estado correcto
    response = {'estado': 'success'}
    return response


def set_status_transaction(request_id, status):

    requests.post('{0}/{1}'.format(CALLBACK_URL, request_id),
                  status,
                  auth=HTTPBasicAuth(CALLBACK_API_KEY,
                                     CALLBACK_API_SECRET))
