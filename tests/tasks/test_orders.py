from datetime import datetime, timedelta
from random import randint
from unittest.mock import MagicMock, patch
import datetime as dt

import pytest
import vcr
from freezegun import freeze_time
from stpmex.exc import (
    AccountDoesNotExist,
    BankCodeClabeMismatch,
    InvalidAccountType,
    InvalidAmount,
    InvalidInstitution,
    InvalidTrackingKey,
    PldRejected,
    StpmexException,
)

from speid.exc import (
    MalformedOrderException,
    ResendSuccessOrderException,
    ScheduleError,
)
from speid.models import Transaction
from speid.tasks.orders import execute, retry_timeout, send_order
from speid.types import Estado, EventType, TipoTransaccion
from speid.validations import factory


@pytest.fixture
def order(physical_account):
    yield dict(
        concepto_pago=f'PRUEBA {randint(0, 9999)}',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=1000,
        nombre_beneficiario='Pablo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante=physical_account.cuenta,
        rfc_curp_ordenante='ND',
        speid_id=f'SP{randint(11111111, 99999999)}',
        version=2,
    )


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


def test_malformed_order_worker(order, mock_callback_queue):
    del order['speid_id']
    with pytest.raises(MalformedOrderException):
        execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error
    transaction.delete()


@pytest.mark.vcr
def test_create_order_debit_card(order, physical_account):
    order['concepto_pago'] = 'DebitCardTest'
    order['cuenta_beneficiario'] = '4242424242424242'
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    assert transaction.events[-1].type is EventType.completed
    assert transaction.tipo is TipoTransaccion.retiro
    transaction.delete()


@pytest.mark.vcr
def test_worker_with_version_2(order, physical_account):
    order['concepto_pago'] = 'PRUEBA Version 2'
    order['version'] = 2
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    assert transaction.events[-1].type is EventType.completed
    assert transaction.tipo is TipoTransaccion.retiro
    transaction.delete()


@pytest.mark.vcr
@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_ignore_invalid_account_type(
    mock_retry: MagicMock,
    mock_capture_exception: MagicMock,
    order,
    physical_account,
    mock_callback_queue,
) -> None:
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
    order,
    physical_account,
    mock_callback_queue,
) -> None:
    order['cuenta_beneficiario'] = '659802025000339321'
    order['institucion_beneficiaria'] = '90659'
    send_order(order)
    mock_retry.assert_not_called()
    mock_capture_exception.assert_not_called()
    transaction = Transaction.objects.order_by('-created_at').first()
    transaction.delete()


@patch('speid.tasks.orders.capture_exception')
def test_malformed_order_exception(
    mock_capture_exception: MagicMock, mock_callback_queue, order
):
    order['cuenta_beneficiario'] = '123456789012345678'
    send_order(order)

    mock_capture_exception.assert_called_once()

    transaction = Transaction.objects.order_by('-created_at').first()
    transaction.delete()


@patch('speid.tasks.orders.execute', side_effect=Exception())
@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_retry_on_unexpected_exception(
    mock_retry: MagicMock, mock_capture_exception: MagicMock, _, order
):
    send_order(order)
    mock_retry.assert_called_once()
    mock_capture_exception.assert_called_once()


def test_hold_max_amount(order):
    order['monto'] = 102000000
    with pytest.raises(MalformedOrderException):
        execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    transaction.delete()


@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_stp_schedule_limit(
    mock_capture_exception: MagicMock, mock_callback_queue, order
):
    with patch('speid.tasks.orders.datetime') as mock_date:
        mock_date.utcnow.return_value = datetime(2020, 9, 1, 23, 57)
        with pytest.raises(ScheduleError):
            execute(order)
        send_order(order)
        mock_capture_exception.assert_called_once()


@vcr.use_cassette('tests/tasks/cassettes/test_resend_not_success_order.yaml')
@pytest.mark.parametrize(
    'exc',
    [
        (AccountDoesNotExist),
        (BankCodeClabeMismatch),
        (InvalidAccountType),
        (InvalidAmount),
        (InvalidInstitution),
        (InvalidTrackingKey),
        (PldRejected),
    ],
)
def test_resend_not_success_order(exc, order, mock_callback_queue):

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
def test_resend_success_order(order):
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    transaction.estado = Estado.succeeded
    transaction.save()
    # Ejecuta nuevamente la misma orden
    with pytest.raises(ResendSuccessOrderException):
        execute(order)
    transaction.delete()


@pytest.mark.vcr()
@freeze_time('2022-11-08 10:00:00')
def test_fail_transaction_with_stp_succeeded(order, mock_callback_queue):
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    # changing time to 4 hours ago so transaction fails in the next step
    transaction.created_at = datetime.utcnow() - timedelta(hours=4)
    transaction.save()
    # executing again so time assert fails
    execute(order)
    # status didn't change because transaction was succesful in STP
    assert transaction.estado is Estado.submitted
    transaction.delete()


@pytest.mark.vcr()
@freeze_time('2022-11-08 10:00:00')
def test_fail_transaction_with_stp_failed(order, mock_callback_queue):
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    # changing time to 4 hours ago so transaction fails in the next step
    transaction.created_at = datetime.utcnow() - timedelta(hours=4)
    transaction.save()
    # executing again so time assert fails
    execute(order)
    # status changed because transaction was failed in STP
    transaction.reload()
    assert transaction.estado is Estado.failed
    transaction.delete()


@pytest.mark.vcr()
@freeze_time('2022-11-08 10:00:00')
def test_fail_transaction_with_no_stp(order, mock_callback_queue):
    # new transaction so next `execute`
    # finds something to send to STP
    input = factory.create(order['version'], **order)
    transaction = input.transform()
    transaction.clave_rastreo = 'CRINEXISTENTE'
    transaction.created_at = datetime.utcnow() - timedelta(hours=4)
    transaction.save()

    # sending to stp
    execute(order)
    transaction.reload()
    # status changed to failed because order was not found in stp
    assert transaction.estado is Estado.failed
    transaction.delete()


@pytest.mark.vcr()
def test_fail_transaction_not_working_day(order, mock_callback_queue):
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    # changing time to 2 days ago so transaction fails in the next step
    transaction.created_at = dt.datetime(2023, 1, 1)
    transaction.save()
    assert not transaction.is_current_working_day()
    # executing again so time assert fails
    execute(order)
    # status didn't change because transaction was succesful in STP
    assert transaction.estado is Estado.submitted
    transaction.delete()


@pytest.mark.vcr
@freeze_time('2022-11-08 10:00:00')
def test_unexpected_stp_error(order, mock_callback_queue):
    with patch(
        'speid.models.transaction.stpmex_client.ordenes.consulta_clave_rastreo'
    ) as consulta_mock, patch(
        'speid.models.transaction.capture_exception'
    ) as capture_mock:
        consulta_mock.side_effect = StpmexException(
            msg="Firma invalida Firma invalida"
        )
        execute(order)
        transaction = Transaction.objects.order_by('-created_at').first()
        assert transaction.estado is Estado.submitted
        # changing time so it fails assertion
        transaction.created_at = datetime.utcnow() - timedelta(hours=4)
        transaction.save()
        # executing again so time assert fails
        execute(order)
        capture_mock.assert_called_once()
