from unittest.mock import MagicMock, patch

import pytest

from speid.models import Account
from speid.tasks.accounts import (
    create_account,
    execute_create_account,
    update_account,
)
from speid.types import Estado
from stpmex.exc import InvalidRfcOrCurp


@pytest.mark.vcr
def test_create_account():
    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
    )

    execute_create_account(account_dict)

    account = Account.objects.get(cuenta='646180157069665325')
    assert account.estado is Estado.succeeded

    account.delete()


def test_create_account_no_name():
    account_dict = dict(
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
    )

    with pytest.raises(TypeError):
        execute_create_account(account_dict)


@pytest.mark.vcr
def test_create_account_existing_account():
    account = Account(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
    )
    account.estado = Estado.error
    account.save()

    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
    )

    execute_create_account(account_dict)

    account = Account.objects.get(cuenta='646180157069665325')
    assert account.estado is Estado.succeeded

    account.delete()


def test_create_account_existing_succeeded_account():
    account = Account(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
    )
    account.estado = Estado.succeeded
    account.stp_id = 123
    account.save()

    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
    )

    execute_create_account(account_dict)

    account = Account.objects.get(cuenta='646180157069665325')
    assert account.estado is Estado.succeeded

    account.delete()


@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.create_account.retry')
def test_does_not_retry_when_validation_error_raised(
    mock_retry: MagicMock, mock_capture_exception: MagicMock
) -> None:
    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp=None,
        telefono='5567980796',
    )
    create_account(account_dict)
    mock_capture_exception.assert_called_once()
    mock_retry.assert_not_called()


@pytest.mark.vcr
@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.create_account.retry')
def test_does_not_retry_when_invalid_rfc_raised(
    mock_retry: MagicMock, mock_capture_exception: MagicMock
) -> None:
    account_dict = dict(
        nombre='24',
        apellido_paterno='napoli',
        apellido_materno='vico pergola sant antonio abate 24',
        cuenta='646180157069665325',
        rfc_curp='VIN2810417HNECPX01',
        telefono='5567980796',
    )
    create_account(account_dict)
    mock_capture_exception.assert_called_once()
    mock_retry.assert_not_called()


@pytest.mark.vcr
@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.create_account.retry')
def test_raises_unexpected_exception(
    mock_retry: MagicMock, mock_capture_exception: MagicMock
) -> None:
    account_dict = dict(
        nombre='24',
        apellido_paterno='napoli',
        apellido_materno='vico pergola sant antonio abate 24',
        cuenta='646180157069665325',
        rfc_curp='VIN2810417HNECPX01',
        telefono='5567980796',
    )
    with patch(
        'speid.tasks.accounts.execute_create_account',
        side_effect=Exception('error!'),
    ):
        create_account(account_dict)
    mock_capture_exception.assert_called_once()
    mock_retry.assert_called_once()


@pytest.mark.vcr
@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.update_account.retry')
def test_update_account_successfully(
    mock_retry: MagicMock, mock_capture_exception: MagicMock
) -> None:
    account_dict = dict(
        nombre='Ric',
        apellido_paterno='San',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
    )

    # debe existir una cuenta guardada en los registros de Account
    with pytest.raises(InvalidRfcOrCurp):
        execute_create_account(account_dict)

    # datos corregidos y nuevo RFC
    account_dict['nombre'] = 'Ricardo'
    account_dict['apellido_paterno'] = 'Sánchez'
    account_dict['apellido_materno'] = 'Castillo'
    account_dict['rfc_curp'] = 'SACR891125HDFABC02'

    update_account(account_dict)

    mock_capture_exception.assert_not_called()
    mock_retry.assert_not_called()

    account = Account.objects.get(cuenta='646180157000000004')
    assert account.nombre == 'Ricardo'
    assert account.apellido_paterno == 'Sánchez'
    assert account.apellido_materno == 'Castillo'
    assert account.rfc_curp == 'SACR891125HDFABC02'
    assert account.estado == Estado.succeeded
    account.delete()


@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.update_account.retry')
def test_update_account_failed_with_validation_error_raised(
    mock_retry: MagicMock, mock_capture_exception: MagicMock
) -> None:
    account_dict = dict(
        nombre='Ric',
        apellido_paterno='San',
        cuenta='646180157000000004',
        rfc_curp=None,
    )

    update_account(account_dict)

    mock_capture_exception.assert_called_once()
    mock_retry.assert_not_called()


@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.update_account.retry')
@patch('speid.tasks.accounts.create_account.apply')
def test_update_account_does_not_exists_then_create_account(
    mock_apply: MagicMock,
    mock_retry: MagicMock,
    mock_capture_exception: MagicMock,
) -> None:
    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
    )

    update_account(account_dict)

    mock_apply.assert_called_once()
    mock_capture_exception.assert_not_called()
    mock_retry.assert_not_called()


@pytest.mark.skip('se deshabilita temporalmente el request a stp')
@pytest.mark.vcr
@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.update_account.retry')
def test_update_account_retries_on_unexpected_exception(
    mock_retry: MagicMock, mock_capture_exception: MagicMock
) -> None:
    account_dict = dict(
        nombre='Ric',
        apellido_paterno='San',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
    )

    # debe existir una cuenta guardada en los registros de Account
    with pytest.raises(InvalidRfcOrCurp):
        execute_create_account(account_dict)

    # datos corregidos y nuevo RFC
    account_dict['nombre'] = 'Ricardo'
    account_dict['apellido_paterno'] = 'Sánchez'
    account_dict['apellido_materno'] = 'Castillo'
    account_dict['rfc_curp'] = 'SACR891125HDFABC02'

    with patch(
        'speid.models.account.stpmex_client.cuentas.update',
        side_effect=Exception('something went wrong!'),
    ):
        update_account(account_dict)

    mock_capture_exception.assert_called_once()
    mock_retry.assert_called_once()

    account = Account.objects.get(cuenta='646180157000000004')

    # los datos no se modifican si falla el update en STP
    assert account.nombre == 'Ric'
    assert account.apellido_paterno == 'San'
    assert not account.apellido_materno
    assert account.rfc_curp == 'SACR891125HDFABC01'
    assert account.estado == Estado.error

    account.delete()
