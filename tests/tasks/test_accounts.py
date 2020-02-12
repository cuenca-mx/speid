from unittest.mock import patch

import pytest
from mongoengine import DoesNotExist

from speid.models import Account
from speid.tasks.accounts import execute, execute_update
from speid.types import Estado


@pytest.mark.vcr
def test_create_account():
    account_dict = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
    )

    execute(account_dict)

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
        execute(account_dict)


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

    execute(account_dict)

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

    execute(account_dict)

    account = Account.objects.get(cuenta='646180157069665325')
    assert account.estado is Estado.succeeded

    account.delete()


def test_update_curp_without_user():
    account_updated = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
    )
    with patch('speid.tasks.accounts.execute_update') as mock_update_curp:
        mock_update_curp.side_effect = DoesNotExist()
        execute_update(account_updated)


@pytest.mark.vcr
def test_update_curp_success_done():
    account = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI01',
        telefono='5567980796',
    )

    execute(account)

    account_updated = dict(
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157069665325',
        rfc_curp='SACR891125HDFGHI02',
        telefono='5567980796',
    )

    execute_update(account_updated)
    account = Account.objects.get(cuenta='646180157069665325')
    assert account.rfc_curp == 'SACR891125HDFGHI02'

    account.delete()
