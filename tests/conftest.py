import datetime as dt
import os
from unittest.mock import patch

import pytest
from celery import Celery

SEND_TRANSACTION_TASK = os.environ['SEND_TRANSACTION_TASK']
SEND_STATUS_TRANSACTION_TASK = os.environ['SEND_STATUS_TRANSACTION_TASK']


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
    # Pongo los import aquí porque de otra forma no puedo hacer tests del
    # __init__ sin que se haya importado ya. Y así no repito el mismo fixture
    # en todos los lugares donde se usa
    from speid.models import PhysicalAccount
    from speid.types import Estado

    account = PhysicalAccount(
        estado=Estado.succeeded,
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
        telefono='5567890123',
        fecha_nacimiento=dt.date(1989, 11, 25),
        pais_nacimiento='MX',
    )
    account.save()

    yield account

    account.delete()
