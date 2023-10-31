import datetime as dt
from datetime import datetime, timedelta
from random import randint
from unittest.mock import MagicMock, patch

import pytest
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
    TransactionNeedManualReviewError,
)
from speid.models import Transaction
from speid.tasks.orders import execute, retry_timeout, send_order
from speid.types import Estado, EventType, TipoTransaccion


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


def test_worker_without_version(default_internal_request, mock_callback_queue):
    default_internal_request['version'] = None

    with pytest.raises(MalformedOrderException):
        execute(default_internal_request)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error


def test_malformed_order_worker(order, mock_callback_queue):
    del order['speid_id']
    with pytest.raises(MalformedOrderException):
        execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.error


@pytest.mark.vcr
def test_create_order_debit_card(order, physical_account):
    order['concepto_pago'] = 'DebitCardTest'
    order['cuenta_beneficiario'] = '4242424242424242'
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    assert transaction.events[-1].type is EventType.completed
    assert transaction.tipo is TipoTransaccion.retiro


@pytest.mark.vcr
def test_worker_with_version_2(order, physical_account):
    order['concepto_pago'] = 'PRUEBA Version 2'
    order['version'] = 2
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    assert transaction.events[-1].type is EventType.completed
    assert transaction.tipo is TipoTransaccion.retiro


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


@patch('speid.tasks.orders.capture_exception')
def test_malformed_order_exception(
    mock_capture_exception: MagicMock, mock_callback_queue, order
):
    order['cuenta_beneficiario'] = '123456789012345678'
    send_order(order)

    mock_capture_exception.assert_called_once()


@patch('speid.tasks.orders.execute', side_effect=Exception())
@patch('speid.tasks.orders.capture_exception')
@patch('speid.tasks.orders.send_order.retry')
def test_retry_on_unexpected_exception(
    mock_retry: MagicMock, mock_capture_exception: MagicMock, _, order
):
    send_order(order)
    mock_retry.assert_called_once()
    mock_capture_exception.assert_called_once()


@patch(
    'speid.tasks.orders.execute',
    side_effect=TransactionNeedManualReviewError('sp1', 'error'),
)
@patch('speid.tasks.orders.capture_exception')
def test_doesnt_retry_on_manual_review_exception(
    mock_capture_exception: MagicMock, _, order
):
    send_order(order)
    mock_capture_exception.assert_called_once()


def test_hold_max_amount(order):
    order['monto'] = 102000000
    with pytest.raises(MalformedOrderException):
        execute(order)


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


@pytest.mark.vcr()
@freeze_time('2023-10-25 14:00:00')
def test_fail_transaction_with_stp_succeeded(
    order, second_physical_account, mock_callback_queue
):
    order['cuenta_ordenante'] = second_physical_account.cuenta
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    # changing time to 4 hours ago so transaction fails in the next step
    transaction.created_at = datetime.utcnow() - timedelta(hours=4)
    # Simulate that we lost `stp_id` for any reason
    transaction.stp_id = None
    transaction.save()
    # executing again so time assert fails
    execute(order)
    # status didn't change because transaction was 'Autorizada' in STP
    assert transaction.estado is Estado.submitted


@pytest.mark.vcr()
@freeze_time('2023-10-31 14:00:00')
def test_transaction_submitted_but_not_found_in_stp(
    order, second_physical_account, mock_callback_queue
):
    order['cuenta_ordenante'] = second_physical_account.cuenta
    execute(order)
    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted
    # simulate that we cannot retrieve transfer data just by changing
    # created_at so the original fecha_operacion changes
    transaction.created_at = transaction.created_at - dt.timedelta(days=1)
    transaction.save()
    with pytest.raises(TransactionNeedManualReviewError):
        execute(order)
    # status didn't change because transaction was 'Autorizada' in STP
    transaction.reload()
    assert transaction.estado is Estado.submitted


@pytest.mark.vcr
@freeze_time('2022-11-08 10:00:00')
def test_unexpected_stp_error(order, mock_callback_queue):
    with patch(
        'speid.models.transaction.stpmex_client.ordenes_v2.'
        'consulta_clave_rastreo_enviada'
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
        transaction.stp_id = None
        transaction.save()
        # executing again so time assert fails
        execute(order)
        capture_mock.assert_called_once()


@pytest.mark.vcr
def test_retry_transfers_with_stp_id_succeeded(
    order, second_physical_account, mock_callback_queue
):
    order['cuenta_ordenante'] = second_physical_account.cuenta

    execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted

    with patch(
        'speid.models.transaction.stpmex_client.ordenes.registra'
    ) as mock_registra:
        execute(order)

    transaction.reload()
    assert transaction.estado is Estado.succeeded
    mock_registra.assert_not_called()


@pytest.mark.vcr
def test_retry_transfers_submitted(
    order, second_physical_account, mock_callback_queue
):
    order['cuenta_ordenante'] = second_physical_account.cuenta
    execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted

    with patch(
        'speid.models.transaction.stpmex_client.ordenes.registra'
    ) as mock_registra:

        execute(order)

    transaction.reload()
    assert transaction.estado is Estado.submitted
    mock_registra.assert_not_called()


@pytest.mark.parametrize(
    'clave_rastreo,speid_estado',
    [
        ('CR1698096580', Estado.failed),  # STP status = Estado.devuelta
        ('CR1698101998', Estado.failed),  # STP status = Estado.cancelada
    ],
)
@pytest.mark.vcr
def test_retrieve_transfer_status_when_stp_id_is_not_none(
    outcome_transaction,
    second_physical_account,
    order,
    clave_rastreo,
    speid_estado,
    mock_callback_queue,
):
    # Transfers that we are passing in the parameter `clave_rastreo`
    # were created on 2023-10-23 23:41 UTC time (fecha_operacion=2023-10-23).
    # STP WS changes the status to `cancelada` or `devuelta` after
    # a few minutes. That's why we cannot create the transfer and then
    # retrieve the status in the same cassette.

    outcome_transaction.created_at = dt.datetime(2023, 10, 23, 23, 41)
    outcome_transaction.cuenta_ordenante = second_physical_account.cuenta
    outcome_transaction.clave_rastreo = clave_rastreo
    outcome_transaction.save()

    order['cuenta_ordenante'] = second_physical_account.cuenta
    order['speid_id'] = outcome_transaction.speid_id

    with patch(
        'speid.models.transaction.stpmex_client.ordenes.registra'
    ) as mock_registra:
        execute(order)

    transfer = Transaction.objects.get(clave_rastreo=clave_rastreo)
    assert transfer.estado is speid_estado
    mock_registra.assert_not_called()


@pytest.mark.vcr
def test_retry_transfers_with_stp_id_but_not_found_in_api(
    order, second_physical_account, mock_callback_queue
):
    order['cuenta_ordenante'] = second_physical_account.cuenta
    execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted

    with patch(
        'speid.models.transaction.Transaction.fetch_stp_status',
        return_value=None,
    ), patch(
        'speid.models.transaction.stpmex_client.ordenes.registra'
    ) as mock_registra:
        with pytest.raises(TransactionNeedManualReviewError):
            execute(order)

    transaction.reload()
    assert transaction.estado is Estado.submitted
    mock_registra.assert_not_called()


@pytest.mark.vcr
def test_retry_transfers_with_stp_id_but_unhandled_status(
    order, second_physical_account, mock_callback_queue
):
    order['cuenta_ordenante'] = second_physical_account.cuenta
    execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    assert transaction.estado is Estado.submitted

    with patch(
        'speid.models.transaction.stpmex_client.ordenes.registra'
    ) as mock_registra:
        with pytest.raises(TransactionNeedManualReviewError):
            execute(order)

    transaction.reload()
    assert transaction.estado is Estado.submitted
    mock_registra.assert_not_called()


@pytest.mark.vcr
def test_retry_transfer_already_failed(
    order, second_physical_account, mock_callback_queue
):
    order['cuenta_ordenante'] = second_physical_account.cuenta
    execute(order)

    transaction = Transaction.objects.order_by('-created_at').first()
    # Changing to error state so we can simulate a failed trx
    transaction.estado = Estado.error
    transaction.save()
    with patch(
        'speid.models.transaction.stpmex_client.ordenes.registra'
    ) as mock_registra:
        execute(order)

    mock_registra.assert_not_called()
