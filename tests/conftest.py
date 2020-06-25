import os
from dataclasses import dataclass

import pytest

from speid.models import Account
from speid.types import Estado

SEND_TRANSACTION_TASK = os.environ['SEND_TRANSACTION_TASK']
SEND_STATUS_TRANSACTION_TASK = os.environ['SEND_STATUS_TRANSACTION_TASK']


@dataclass
class Response:
    status_code: int
    text: str


def substitute_patch_status(*_, **__):
    return Response(status_code=201, text='{"status": "succeeded"}')


@pytest.fixture
def mock_callback_api(monkeypatch):
    import requests

    monkeypatch.setattr(requests, 'patch', substitute_patch_status)
    monkeypatch.setattr(requests, 'post', substitute_patch_status)


def substitute_patch_status_fail(*_, **__):
    return Response(status_code=403, text='{"status": "failed"}')


@pytest.fixture
def mock_callback_api_fail(monkeypatch):
    import requests

    monkeypatch.setattr(requests, 'patch', substitute_patch_status_fail)
    monkeypatch.setattr(requests, 'post', substitute_patch_status_fail)


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
