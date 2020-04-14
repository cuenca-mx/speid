from unittest.mock import MagicMock, patch

import pytest

from speid.exc import MalformedOrderException
from speid.models import Transaction
from speid.tasks.orders import execute, send_order
from speid.types import Estado, EventType


@pytest.mark.usefixtures('mock_callback_api')
def test_worker_with_incorrect_version(default_internal_request):
    default_internal_request['version'] = 0

    with pytest.raises(MalformedOrderException):
        execute(default_internal_request)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error
    transaction.delete()


@pytest.mark.usefixtures('mock_callback_api')
def test_worker_without_version(default_internal_request):
    default_internal_request['version'] = None

    with pytest.raises(MalformedOrderException):
        execute(default_internal_request)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error
    transaction.delete()


@pytest.mark.usefixtures('mock_callback_api')
def test_malformed_order_worker():
    order = dict(
        concepto_pago='PRUEBA',
        institucion_ordenante='646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        version=2,
    )
    with pytest.raises(MalformedOrderException):
        execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error
    transaction.delete()


@pytest.mark.vcr
@pytest.mark.usefixtures('create_account')
def test_create_order_debit_card():
    order = dict(
        concepto_pago='DebitCardTest',
        institucion_ordenante='90646',
        cuenta_beneficiario='4242424242424242',
        institucion_beneficiaria='40072',
        monto=1020,
        nombre_beneficiario='Pach',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='5694433',
        version=2,
    )
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    assert transaction.events[-1].type is EventType.completed
    transaction.delete()


@pytest.mark.vcr
@pytest.mark.usefixtures('create_account')
def test_worker_with_version_2():
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=1020,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='ANOTHER_RANDOM_ID',
        version=2,
    )
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    assert transaction.events[-1].type is EventType.completed
    transaction.delete()


@pytest.mark.vcr
@pytest.mark.usefixtures('create_account')
@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_ignore_invalid_account_type(
    mock_retry: MagicMock, mock_capture_exception: MagicMock
) -> None:
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=1020,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='ANOTHER_RANDOM_ID',
        version=2,
    )
    send_order(order)
    mock_retry.assert_not_called()
    mock_capture_exception.assert_not_called()
    transaction = Transaction.objects.order_by('-created_at').first()
    transaction.delete()
