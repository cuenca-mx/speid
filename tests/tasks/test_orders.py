from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
import vcr
from stpmex.exc import (
    AccountDoesNotExist,
    BankCodeClabeMismatch,
    InvalidAccountType,
    InvalidAmount,
    InvalidInstitution,
    InvalidTrackingKey,
    PldRejected,
)

from speid.exc import (
    MalformedOrderException,
    ResendSuccessOrderException,
    ScheduleError,
)
from speid.models import Transaction
from speid.tasks.orders import execute, retry_timeout, send_order
from speid.types import Estado, EventType


@pytest.mark.parametrize(
    'attempts, expected', [(1, 2), (5, 10), (10, 1200), (15, 1200)]
)
def test_retry_timeout(attempts, expected):
    assert retry_timeout(attempts) == expected


def test_worker_with_incorrect_version(
    default_internal_request, mock_callback_queue
):
    default_internal_request['version'] = 0

    with pytest.raises(MalformedOrderException):
        execute(default_internal_request)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error
    transaction.delete()


def test_worker_without_version(default_internal_request, mock_callback_queue):
    default_internal_request['version'] = None

    with pytest.raises(MalformedOrderException):
        execute(default_internal_request)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error
    transaction.delete()


def test_malformed_order_worker(mock_callback_queue):
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
def test_create_order_debit_card(physical_account):
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
def test_worker_with_version_2(physical_account):
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
@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_ignore_invalid_account_type(
    mock_retry: MagicMock,
    mock_capture_exception: MagicMock,
    physical_account,
    mock_callback_queue,
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


@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_ignore_transfers_to_blocked_banks(
    mock_retry: MagicMock,
    mock_capture_exception: MagicMock,
    physical_account,
    mock_callback_queue,
) -> None:
    order = dict(
        concepto_pago='PRUEBA bloqueo',
        institucion_ordenante='90646',
        cuenta_beneficiario='659802025000339321',
        institucion_beneficiaria='90659',
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


@patch('speid.tasks.orders.capture_exception')
def test_malformed_order_exception(
    mock_capture_exception: MagicMock, mock_callback_queue
):
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_ordenante='90646',
        cuenta_beneficiario='123456789012345678',
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

    mock_capture_exception.assert_called_once()

    transaction = Transaction.objects.order_by('-created_at').first()
    transaction.delete()


@patch('speid.tasks.orders.execute', side_effect=Exception())
@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_retry_on_unexpected_exception(
    mock_retry: MagicMock, mock_capture_exception: MagicMock, _
):
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
    mock_retry.assert_called_once()
    mock_capture_exception.assert_called_once()


def test_hold_max_amount():
    order = dict(
        concepto_pago='PRUEBA Version 2',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=102000000,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='stp_id_again',
        version=2,
    )
    with pytest.raises(MalformedOrderException):
        execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    transaction.delete()


@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_stp_schedule_limit(
    mock_capture_exception: MagicMock, mock_callback_queue
):
    with patch('speid.tasks.orders.datetime') as mock_date:
        mock_date.utcnow.return_value = datetime(2020, 9, 1, 23, 57)
        order = dict(
            concepto_pago='PRUEBA Version 2',
            institucion_ordenante='90646',
            cuenta_beneficiario='072691004495711499',
            institucion_beneficiaria='40072',
            monto=102000000,
            nombre_beneficiario='Pablo Sánchez',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND',
            speid_id='stp_id_again',
            version=2,
        )
        with pytest.raises(ScheduleError):
            execute(order)
        send_order(order)
        mock_capture_exception.assert_called_once()


@vcr.use_cassette('tests/tasks/cassettes/test_resend_not_success_order.yaml')
@pytest.mark.parametrize(
    'exc',
    [
        (AccountDoesNotExist),
        (AssertionError),
        (BankCodeClabeMismatch),
        (InvalidAccountType),
        (InvalidAmount),
        (InvalidInstitution),
        (InvalidTrackingKey),
        (PldRejected),
    ],
)
def test_resend_not_success_order(exc, physical_account, mock_callback_queue):
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
        speid_id='stp_id_again',
        version=2,
    )

    with patch(
        'speid.tasks.orders.Transaction.create_order',
        side_effect=exc(),
    ):
        execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.failed

    # Ejecuta nuevamente la misma orden
    execute(order)

    transaction.reload()
    assert transaction.events[-2].type is EventType.retry
    assert transaction.estado is Estado.submitted

    transaction.delete()


@pytest.mark.vcr
def test_resend_success_order(physical_account):
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
        speid_id='stp_id_again',
        version=2,
    )
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    transaction.estado = Estado.succeeded
    transaction.save()
    # Ejecuta nuevamente la misma orden
    with pytest.raises(ResendSuccessOrderException):
        execute(order)
    transaction.delete()
