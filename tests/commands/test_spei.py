import datetime as dt

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


@pytest.mark.usefixtures('mock_callback_queue')
@pytest.mark.vcr
def test_reconciliate_deposits_historic(runner):
    """
    Esta prueba simula obtener depósitos de días históricos, es decir, de
    depósitos que llegaron en días operativos anteriores al día operativo
    en curso
    """

    fecha_operacion = dt.date(2023, 11, 6)

    initial_deposits_count = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).count()

    assert initial_deposits_count == 0

    runner.invoke(
        speid_group,
        [
            'reconciliate-deposits',
            fecha_operacion.strftime('%Y-%m-%d'),
            'PruebaLiquidacion2,PruebaDevolucion1',
        ],
    )

    deposits_db = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).all()

    assert len(deposits_db) == 1
    assert deposits_db[0].clave_rastreo == 'PruebaLiquidacion2'
    assert deposits_db[0].monto == 1_00

    # Al ejecutar el comando con las mismas claves de rastreo no debe
    # duplicar los depósitos
    runner.invoke(
        speid_group,
        [
            'reconciliate-deposits',
            fecha_operacion.strftime('%Y-%m-%d'),
            'PruebaLiquidacion2,PruebaDevolucion1',
        ],
    )

    deposits_db = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).all()

    assert len(deposits_db) == 1
    assert deposits_db[0].clave_rastreo == 'PruebaLiquidacion2'
