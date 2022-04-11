import base64
import os
from typing import Optional

from celery import Celery

BROKER = os.environ['AMPQ_ADDRESS']
SEND_TRANSACTION_TASK = os.environ['SEND_TRANSACTION_TASK']
SEND_STATUS_TRANSACTION_TASK = os.environ['SEND_STATUS_TRANSACTION_TASK']


def auth_header(username: str, password: str) -> dict:
    creds = base64.b64encode(f'{username}:{password}'.encode('ascii')).decode(
        'utf-8'
    )
    return dict(Authorization=f'Basic {creds}')


def set_status_transaction(
    speid_id: str,
    state: str,
    curp: Optional[str] = None,
    rfc: Optional[str] = None,
) -> None:
    queue = Celery('back_end_client', broker=BROKER)
    queue.send_task(
        SEND_STATUS_TRANSACTION_TASK,
        kwargs=dict(
            speid_id=speid_id,
            state=state,
            rfc=rfc,
            curp=curp,
        ),
    )


def send_transaction(transaction: dict):
    queue = Celery('back_end_client', broker=BROKER)
    queue.send_task(
        SEND_TRANSACTION_TASK, kwargs=dict(transaction=transaction)
    )
