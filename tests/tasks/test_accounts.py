import pytest

from speid.models import Account
from speid.tasks.accounts import execute
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
