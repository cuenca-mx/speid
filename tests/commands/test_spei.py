import datetime as dt
import json

import pytest
import requests_mock
from freezegun import freeze_time

from speid.commands.spei import (
    ESTADOS_DEPOSITOS_VALIDOS,
    TIPOS_PAGO_DEVOLUCION,
    speid_group,
)
from speid.models import Transaction
from speid.types import Estado, EventType
from speid.validations import StpTransaction


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


@freeze_time("2023-08-26 01:00:00")  # 2023-08-25 19:00 UTC-6
@pytest.mark.usefixtures('mock_callback_queue')
def test_reconciliate_deposits_historic(runner):
    """
    Esta prueba simula obtener depósitos de días históricos, es decir, de
    depósitos que llegaron en días operativos anteriores al día operativo
    en curso
    """

    fecha_operacion = dt.date(2023, 8, 25)

    initial_deposits_count = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).count()

    assert initial_deposits_count == 0

    with open('tests/commands/deposits_20230825.json') as f:
        stp_response = json.loads(f.read())
        deposits = stp_response['resultado']['lst']

    valid_deposits = [
        d
        for d in deposits
        if d['estado'] in ESTADOS_DEPOSITOS_VALIDOS
        and d['tipoPago'] not in TIPOS_PAGO_DEVOLUCION
    ]

    with requests_mock.mock() as m:
        m.post('/speiws/rest/ordenPago/consOrdenesFech', json=stp_response)

        runner.invoke(
            speid_group,
            [
                'reconciliate-deposits',
                fecha_operacion.strftime('%Y-%m-%d'),
                deposits[0]['claveRastreo'],
            ],
        )

    deposits = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).all()

    assert len(deposits) == len(valid_deposits)
    Transaction.drop_collection()


@freeze_time("2023-08-27")  # 2023-08-26 18:00 UTC-6
@pytest.mark.usefixtures('mock_callback_queue')
def test_reconciliate_deposits_current_fecha_operacion(runner):
    """
    Esta prueba simula obtener depósitos del día operativo en curso
    """
    fecha_operacion = dt.date(2023, 8, 28)

    initial_deposits_count = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).count()

    assert initial_deposits_count == 0

    with open('tests/commands/deposits_20230828.json') as f:
        stp_response = json.loads(f.read())
        deposits = stp_response['resultado']['lst']

    claves_rastreo = ','.join(d['claveRastreo'] for d in deposits)
    devolucion = next(d for d in deposits if d['estado'] == 'D')
    valid_deposits = [
        d
        for d in deposits
        if d['estado'] in ESTADOS_DEPOSITOS_VALIDOS
        and d['tipoPago'] not in TIPOS_PAGO_DEVOLUCION
    ]

    with requests_mock.mock() as m:
        m.post('/speiws/rest/ordenPago/consOrdenesFech', json=stp_response)

        runner.invoke(
            speid_group,
            [
                'reconciliate-deposits',
                fecha_operacion.strftime('%Y-%m-%d'),
                claves_rastreo,
            ],
        )

    deposits = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).all()

    assert len(deposits) == len(valid_deposits)
    assert not any(
        d.clave_rastreo == devolucion['claveRastreo'] for d in deposits
    )
    Transaction.drop_collection()


@freeze_time("2023-08-26 01:00:00")  # 2023-08-25 19:00 UTC-6
@pytest.mark.usefixtures('mock_callback_queue')
def test_reconciliate_deposits_ignores_duplicated(runner):
    """
    Esta prueba simula obtener depósitos de días históricos. Ignora depósitos
    que ya existen en speid
    """
    fecha_operacion = dt.date(2023, 8, 25)

    initial_deposits_count = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).count()

    assert initial_deposits_count == 0

    with open('tests/commands/deposits_20230825.json') as f:
        stp_response = json.loads(f.read())
        deposits = stp_response['resultado']['lst']

    deposit = deposits[0]
    claves_rastreo = ','.join(d['claveRastreo'] for d in deposits)
    external_tx = StpTransaction(  # type: ignore
        Clave=deposit['idEF'],
        FechaOperacion=deposit['fechaOperacion'],
        InstitucionOrdenante=deposit['institucionContraparte'],
        InstitucionBeneficiaria=deposit['institucionOperante'],
        ClaveRastreo=deposit['claveRastreo'],
        Monto=deposit['monto'],
        NombreOrdenante=deposit['nombreOrdenante'],
        TipoCuentaOrdenante=deposit['tipoCuentaOrdenante'],
        CuentaOrdenante=deposit['cuentaOrdenante'],
        RFCCurpOrdenante=deposit['rfcCurpOrdenante'],
        NombreBeneficiario=deposit['nombreBeneficiario'],
        TipoCuentaBeneficiario=deposit['tipoCuentaBeneficiario'],
        CuentaBeneficiario=deposit['cuentaBeneficiario'],
        RFCCurpBeneficiario='NA',
        ConceptoPago=deposit['conceptoPago'],
        ReferenciaNumerica=deposit['referenciaNumerica'],
        Empresa=deposit['empresa'],
    )
    transaction = external_tx.transform()
    transaction.estado = Estado.succeeded
    transaction.save()

    valid_deposits = [
        d
        for d in deposits
        if d['estado'] in ESTADOS_DEPOSITOS_VALIDOS
        and d['tipoPago'] not in TIPOS_PAGO_DEVOLUCION
    ]

    with requests_mock.mock() as m:
        m.post('/speiws/rest/ordenPago/consOrdenesFech', json=stp_response)

        runner.invoke(
            speid_group,
            [
                'reconciliate-deposits',
                fecha_operacion.strftime('%Y-%m-%d'),
                claves_rastreo,
            ],
        )

    deposits = Transaction.objects(
        tipo='deposito', fecha_operacion=fecha_operacion
    ).all()

    assert len(deposits) == len(valid_deposits)
    Transaction.drop_collection()
