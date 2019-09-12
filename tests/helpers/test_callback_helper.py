import json
from datetime import datetime

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


def test_send_transaction(mock_callback_api):
    transaction = Transaction(
        fecha_operacion=datetime.today(),
        institucion_ordenante=40012,
        institucion_beneficiaria=90646,
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
    )
    res = send_transaction(transaction.to_dict())
    assert res['status'] == 'succeeded'


def test_set_status_transaction(mock_callback_api):
    res = set_status_transaction(123, 'success')
    assert res.status_code == 201
    assert json.loads(res.text)['status'] == 'succeeded'
