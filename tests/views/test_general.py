from unittest.mock import patch

import pytest
from celery import Celery

from speid.models import Transaction
from speid.types import Estado


def test_ping(client):
    res = client.get('/')
    assert res.status_code == 200


def test_health_check(client):
    res = client.get('/healthcheck')
    assert res.status_code == 200


@pytest.mark.usefixtures('mock_callback_queue')
def test_create_order_event(client, default_outcome_transaction):
    data = dict(
        id=default_outcome_transaction.stp_id,
        Estado='LIQUIDACION',
        Detalle="0",
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=default_outcome_transaction.id)
    assert trx.estado is Estado.succeeded


@pytest.mark.usefixtures('mock_callback_queue')
def test_create_order_event_failed_twice(client, default_outcome_transaction):
    data = dict(
        id=default_outcome_transaction.stp_id, Estado='DEVOLUCION', Detalle="0"
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=default_outcome_transaction.id)
    assert trx.estado is Estado.failed

    num_events = len(trx.events)
    data = dict(
        id=default_outcome_transaction.stp_id, Estado='DEVOLUCION', Detalle="0"
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=default_outcome_transaction.id)
    assert trx.estado is Estado.failed
    assert len(trx.events) == num_events


@pytest.mark.usefixtures('mock_callback_queue')
def test_cancelled_transaction(client, default_outcome_transaction) -> None:
    data = dict(
        id=default_outcome_transaction.stp_id,
        Estado='CANCELACION',
        Detalle="0",
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=default_outcome_transaction.id)
    assert trx.estado is Estado.failed


def test_invalid_order_event(client, default_outcome_transaction):
    data = dict(Estado='LIQUIDACION', Detalle="0")
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=default_outcome_transaction.id)
    assert trx.estado is Estado.created
    trx.delete()


def test_invalid_id_order_event(client, default_outcome_transaction):
    data = dict(id='9', Estado='LIQUIDACION', Detalle="0")
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=default_outcome_transaction.id)
    assert trx.estado is Estado.created
    trx.delete()


@pytest.mark.usefixtures('mock_callback_queue')
def test_order_event_duplicated(client, default_outcome_transaction):
    data = dict(
        id=default_outcome_transaction.stp_id,
        Estado='LIQUIDACION',
        Detalle="0",
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    data = dict(
        id=default_outcome_transaction.stp_id, Estado='DEVOLUCION', Detalle="0"
    )
    resp = client.post('/orden_events', json=data)
    assert resp.status_code == 200
    assert resp.data == "got it!".encode()

    trx = Transaction.objects.get(id=default_outcome_transaction.id)
    assert trx.estado is Estado.failed
    trx.delete()


@pytest.mark.usefixtures('mock_callback_queue')
def test_create_orden(client, default_income_transaction):
    resp = client.post('/ordenes', json=default_income_transaction)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.succeeded
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'
    transaction.delete()


@pytest.mark.usefixtures('mock_callback_queue')
def test_create_mal_formed_orden(client):
    request = {
        "Clave": 17658976,
        "ClaveRastreo": "clave-restreo",
        "CuentaOrdenante": "014180567802222244",
        "FechaOperacion": 20200416,
        "InstitucionBeneficiaria": 90646,
        "InstitucionOrdenante": 40014,
        "Monto": 500,
        "NombreOrdenante": "Pepito",
        "RFCCurpOrdenante": "XXXX950221141",
        "TipoCuentaOrdenante": 40,
    }
    resp = client.post('/ordenes', json=request)
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'


@pytest.mark.usefixtures('mock_callback_queue')
def test_create_orden_duplicated(client, default_income_transaction):
    resp = client.post('/ordenes', json=default_income_transaction)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.succeeded
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'

    default_income_transaction['Clave'] = 2456304
    resp = client.post('/ordenes', json=default_income_transaction)
    transactions = Transaction.objects(
        clave_rastreo=default_income_transaction['ClaveRastreo']
    ).order_by('-created_at')
    assert len(transactions) == 1
    assert transactions[0].stp_id == 2456303
    assert transactions[0].estado is Estado.succeeded
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'
    for t in transactions:
        t.delete()


@pytest.mark.usefixtures('mock_callback_queue')
def test_create_orden_blocked(client, default_blocked_transaction):
    resp = client.post('/ordenes', json=default_blocked_transaction)
    transaction = Transaction.objects.get(
        stp_id=default_blocked_transaction['Clave']
    )
    assert transaction.estado is Estado.error
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'
    transaction.delete()


@pytest.mark.usefixtures('mock_callback_queue')
def test_create_incoming_orden_blocked(
    client, default_blocked_incoming_transaction
):
    resp = client.post('/ordenes', json=default_blocked_incoming_transaction)
    transaction = Transaction.objects.get(
        stp_id=default_blocked_incoming_transaction['Clave']
    )
    assert transaction.estado is Estado.error
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'
    transaction.delete()


def test_create_orden_exception(client, default_income_transaction):
    with patch.object(
        Celery, 'send_task', side_effect=Exception('Algo muy malo')
    ):
        resp = client.post('/ordenes', json=default_income_transaction)
        transaction = Transaction.objects.order_by('-created_at').first()
        assert transaction.estado is Estado.error
        assert resp.status_code == 201
        assert resp.json['estado'] == 'LIQUIDACION'
        transaction.delete()


@pytest.mark.usefixtures('mock_callback_queue')
def test_create_orden_without_ordenante(client):
    data = dict(
        Clave=123123233,
        FechaOperacion=20190129,
        InstitucionOrdenante=40102,
        InstitucionBeneficiaria=90646,
        ClaveRastreo='MANU-00000295251',
        Monto=1000,
        NombreOrdenante='null',
        TipoCuentaOrdenante=0,
        CuentaOrdenante='null',
        RFCCurpOrdenante='null',
        NombreBeneficiario='JESUS ADOLFO ORTEGA TURRUBIATES',
        TipoCuentaBeneficiario=40,
        CuentaBeneficiario='646180157020812599',
        RFCCurpBeneficiario='ND',
        ConceptoPago='FONDEO',
        ReferenciaNumerica=1232134,
        Empresa='TAMIZI',
    )
    resp = client.post('/ordenes', json=data)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.succeeded
    assert resp.status_code == 201
    assert resp.json['estado'] == 'LIQUIDACION'
    transaction.delete()
