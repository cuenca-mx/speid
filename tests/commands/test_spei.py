import pytest

from speid.commands.spei import speid_group
from speid.models import Transaction
from speid.types import Estado, EventType


@pytest.fixture
def transaction():
    transaction = Transaction(
        concepto_pago='PRUEBA',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='speid_id',
    )
    transaction.save()

    yield transaction

    transaction.delete()


def test_callback_spei_transaction(runner, mock_callback_queue, transaction):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    runner.invoke(
        speid_group, ['callback-spei-transaction', str(id_trx), 'succeeded']
    )

    transaction = Transaction.objects.get(id=id_trx)
    assert transaction.estado is Estado.succeeded
    assert transaction.events[-1].type is EventType.completed
    assert transaction.events[-1].metadata == 'Reversed by SPEID command'


def test_callback_spei_failed_transaction(
    runner, mock_callback_queue, transaction
):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    runner.invoke(
        speid_group, ['callback-spei-transaction', str(id_trx), 'failed']
    )

    transaction = Transaction.objects.get(id=id_trx)
    assert transaction.estado is Estado.failed
    assert transaction.events[-1].type is EventType.error
    assert transaction.events[-1].metadata == 'Reversed by SPEID command'


def test_callback_spei_invalid_transaction(
    runner, mock_callback_queue, transaction
):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    result = runner.invoke(
        speid_group, ['callback-spei-transaction', str(id_trx), 'invalid']
    )

    transaction = Transaction.objects.get(id=id_trx)
    assert transaction.estado is Estado.created
    assert type(result.exception) is ValueError


@pytest.mark.vcr
def test_re_execute_transactions(runner, transaction, physical_account):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    runner.invoke(
        speid_group, ['re-execute-transactions', transaction.speid_id]
    )

    transaction = Transaction.objects.get(id=id_trx)

    assert transaction.estado is Estado.submitted
    assert transaction.events[-1].type is EventType.completed


def test_re_execute_transaction_not_found(
    runner, transaction, physical_account
):
    id_trx = transaction.id
    assert transaction.estado is Estado.created

    result = runner.invoke(
        speid_group, ['re-execute-transactions', 'invalid_speid_id']
    )
    transaction = Transaction.objects.get(id=id_trx)

    assert transaction.estado is Estado.created
    assert type(result.exception) is ValueError
