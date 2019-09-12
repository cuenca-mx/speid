import pytest

from speid.commands.spei import (callback_spei_transaction,
                                 re_execute_transactions)
from speid.models import Transaction
from speid.types import Estado, EventType


@pytest.mark.skip(reason="Commands test")
def test_callback_spei_transaction(runner, mock_callback_api):
    transaction = Transaction(
        concepto_pago='PRUEBA',
        institucion_ordenante='646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='speid_id',
    )
    transaction.save()
    id_trx = transaction.id
    assert transaction.estado is Estado.submitted

    runner.invoke(callback_spei_transaction,
                  ['transaction_id', id_trx,
                   'transaction_status', 'succeeded'])

    transaction = Transaction.objects.get(id=id_trx)
    assert transaction.estado is Estado.succeeded
    assert transaction.events[-1].type is EventType.completed
    assert transaction.events[-1].metadata == 'Reverse by command SPEID'

    transaction.delete()


@pytest.mark.vcr
@pytest.mark.skip(reason="Commands test")
def test_re_execute_transactions(runner):
    transaction = Transaction(
        concepto_pago='PRUEBA',
        institucion_ordenante='646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='speid_id',
    )
    transaction.save()
    id_trx = transaction.id

    runner.invoke(re_execute_transactions, ['--speid_id', 'speid_id'])

    transaction = Transaction.objects.get(id=id_trx)

    assert transaction.estado is Estado.submitted
    assert transaction.events[-1].type is EventType.completed
