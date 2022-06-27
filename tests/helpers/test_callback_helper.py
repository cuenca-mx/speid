from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from speid.helpers.callback_helper import (
    auth_header,
    send_transaction,
    set_status_transaction,
)
from speid.models import Transaction


def test_auth_header():
    user = 'TESTING'
    password = 'PASSWORD'
    auth = auth_header(user, password)
    assert type(auth) is dict
    assert auth['Authorization'] is not None
    assert auth['Authorization'] == 'Basic VEVTVElORzpQQVNTV09SRA=='


@patch('speid.helpers.callback_helper.Celery.send_task')
def test_send_transaction(mock_send_transaction: MagicMock):
    params = dict(
        fecha_operacion=datetime.now(),
        institucion_ordenante='40012',
        institucion_beneficiaria='90646',
        clave_rastreo="PRUEBATAMIZI1",
        monto=100.0,
        nombre_ordenante="BANCO",
        tipo_cuenta_ordenante=40,
        cuenta_ordenante="846180000500000008",
        rfc_curp_ordenante="ND",
        nombre_beneficiario="TAMIZI",
        tipo_cuenta_beneficiario=40,
        cuenta_beneficiario="646180157000000004",
        rfc_curp_beneficiario="ND",
        concepto_pago="PRUEBA",
        referencia_numerica=2423,
        empresa="TAMIZI",
        tipo_transaccion='deposito',
    )

    transaction = Transaction(**params)
    send_transaction(transaction.to_dict())

    task_params = mock_send_transaction.call_args[1]['kwargs']['transaction']

    for param, value in params.items():
        if param == 'fecha_operacion':
            continue
        assert value == task_params[param]
    assert (
        params['fecha_operacion'].isoformat() == task_params['fecha_operacion']
    )


@patch('speid.helpers.callback_helper.Celery.send_task')
@pytest.mark.parametrize(
    "speid_id, state",
    [pytest.param('UN_ID', 'success'), pytest.param('DOS_ID', 'fail')],
)
def test_set_status_transaction(
    mock_set_status_transaction: MagicMock, speid_id: str, state: str
):
    params = dict(speid_id=speid_id, state=state)
    set_status_transaction(**params)

    task_params = mock_set_status_transaction.call_args[1]['kwargs']
    assert all(params[param] == task_params[param] for param in params)
