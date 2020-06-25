import os
from dataclasses import dataclass
from unittest.mock import patch

import pytest
from celery import Celery

from speid.models import Account
from speid.types import Estado

SEND_TRANSACTION_TASK = os.environ['SEND_TRANSACTION_TASK']
SEND_STATUS_TRANSACTION_TASK = os.environ['SEND_STATUS_TRANSACTION_TASK']


@dataclass
class Response:
    status_code: int
    text: str


@pytest.fixture
def mock_callback_queue():
    with patch.object(Celery, 'send_task', return_value=None):
        yield


@pytest.fixture(scope='module')
def vcr_config():
    config = dict()
    config['record_mode'] = 'none'
    return config


@pytest.fixture
def create_account():
    account = Account(
        estado=Estado.succeeded,
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
        telefono='5567890123',
    )
    account.save()

    yield account

    account.delete()
