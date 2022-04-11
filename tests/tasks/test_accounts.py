import datetime as dt
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError
from stpmex.exc import InvalidRfcOrCurp

from speid.models import PhysicalAccount
from speid.models.account import MoralAccount
from speid.tasks.accounts import (
    create_account,
    deactivate_account,
    execute_create_account,
    update_account,
)
from speid.types import Estado


@pytest.mark.vcr
def test_create_account():
    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
        fecha_nacimiento='1994-04-19T00:00:00',
        pais_nacimiento='MX',
    )

    execute_create_account(account_dict)

    account = PhysicalAccount.objects.get(cuenta='646180157069665325')
    assert account.estado is Estado.succeeded

    account.delete()


@pytest.mark.vcr
def test_create_moral_account():
    account_dict = dict(
        type='asfasdf',
        nombre='TARJETAS CUENCA',
        rfc_curp='TCU200828RX8',
        cuenta='646180157062429678',
        fecha_constitucion='2021-01-01T00:00:00',
        pais='MX',
        allowed_rfc='POHF880201R4H',
        allowed_curp='POHF880201MCSKRL09',
    )

    execute_create_account(account_dict)

    account = MoralAccount.objects.get(cuenta='646180157062429678')
    assert account.estado is Estado.succeeded
    assert account.nombre == 'TARJETAS CUENCA'
    assert account.allowed_curp == 'POHF880201MCSKRL09'
    assert account.allowed_rfc == 'POHF880201R4H'
    assert account.rfc_curp == 'TCU200828RX8'
    assert account.fecha_constitucion == dt.datetime(2021, 1, 1)
    assert account.pais == 'MX'
    assert not account.entidad_federativa
    assert not account.actividad_economica
    account.delete()


def test_create_account_no_name():
    account_dict = dict(
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
    )

    with pytest.raises(ValidationError):
        execute_create_account(account_dict)


@pytest.mark.vcr
def test_create_account_existing_account():
    account = PhysicalAccount(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
        fecha_nacimiento=dt.datetime(1989, 11, 25),
        pais_nacimiento='MX',
    )
    account.estado = Estado.error
    account.save()

    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
        fecha_nacimiento='1994-04-19T00:00:00',
        pais_nacimiento='MX',
    )

    execute_create_account(account_dict)

    account = PhysicalAccount.objects.get(cuenta='646180157069665325')
    assert account.estado is Estado.succeeded

    account.delete()


def test_create_account_existing_succeeded_account():
    account = PhysicalAccount(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
        fecha_nacimiento=dt.datetime(1989, 11, 25),
        pais_nacimiento='MX',
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
        fecha_nacimiento='1994-04-19T00:00:00',
        pais_nacimiento='MX',
    )

    execute_create_account(account_dict)

    account = PhysicalAccount.objects.get(cuenta='646180157069665325')
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
        fecha_nacimiento='1994-04-19T00:00:00',
        pais_nacimiento='MX',
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
        fecha_nacimiento=dt.date(1989, 11, 25),
        pais_nacimiento='MX',
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
        fecha_nacimiento='1994-04-19T00:00:00',
        pais_nacimiento='MX',
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

    account = PhysicalAccount.objects.get(cuenta='646180157000000004')
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
        fecha_nacimiento=dt.date(1989, 11, 25),
        pais_nacimiento='MX',
    )

    update_account(account_dict)

    mock_capture_exception.assert_called_once()
    mock_retry.assert_not_called()


@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.update_account.retry')
@patch('speid.tasks.accounts.create_account.apply_async')
def test_update_account_does_not_exists_then_create_account(
    mock_apply: MagicMock,
    mock_retry: MagicMock,
    mock_capture_exception: MagicMock,
) -> None:
    account_dict = dict(
        type='physical',
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
        fecha_nacimiento='1994-04-19T00:00:00',
        pais_nacimiento='MX',
    )

    update_account(account_dict)

    mock_apply.assert_called_once()
    mock_capture_exception.assert_not_called()
    mock_retry.assert_not_called()


@pytest.mark.vcr
@patch(
    'speid.tasks.accounts.PhysicalAccountValidation', side_effect=Exception()
)
@patch('speid.tasks.accounts.capture_exception')
@patch('speid.tasks.accounts.update_account.retry', return_value=None)
def test_update_account_retries_on_unexpected_exception(
    mock_retry: MagicMock, mock_capture_exception: MagicMock, _
) -> None:
    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
    )

    update_account(account_dict)

    mock_capture_exception.assert_called_once()
    mock_retry.assert_called_once()


@pytest.mark.vcr
@patch('speid.tasks.accounts.deactivate_account.retry')
def test_deactivate_account(
    mock_retry: MagicMock,
):
    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
        fecha_nacimiento='1994-04-19T00:00:00',
        pais_nacimiento='MX',
    )
    # Crea la cuenta
    execute_create_account(account_dict)
    account = PhysicalAccount.objects.get(cuenta='646180157069665325')
    assert account.estado == Estado.succeeded
    # Elimina la cuenta
    deactivate_account(account.cuenta)
    account = PhysicalAccount.objects.get(cuenta=account.cuenta)
    assert account.estado == Estado.deactivated
    deactivate_account(account.cuenta)
    mock_retry.assert_called_once()


@patch('speid.tasks.accounts.deactivate_account.retry')
def test_deactivate_account_doesnot_exist(
    mock_retry: MagicMock,
):
    deactivate_account('646180157000011122')
    mock_retry.assert_not_called()
