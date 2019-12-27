import pytest
from pydantic import ValidationError
from stpmex.types import TipoCuenta

from speid.models import Event, Transaction
from speid.types import Estado, EventType
from speid.validations import SpeidTransaction, StpTransaction


def test_transaction():
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
    transaction.events.append(Event(type=EventType.created))
    transaction.events.append(Event(type=EventType.received))
    transaction.events.append(Event(type=EventType.retry))
    transaction.events.append(Event(type=EventType.retry))
    transaction.events.append(Event(type=EventType.error))
    transaction.events.append(Event(type=EventType.completed))

    transaction.save()
    trx_saved = Transaction.objects.get(id=transaction.id)
    assert transaction.concepto_pago == trx_saved.concepto_pago
    assert transaction.institucion_beneficiaria == (
        trx_saved.institucion_beneficiaria
    )
    assert transaction.cuenta_beneficiario == trx_saved.cuenta_beneficiario
    assert transaction.institucion_beneficiaria == (
        trx_saved.institucion_beneficiaria
    )
    assert transaction.monto == trx_saved.monto
    assert transaction.nombre_beneficiario == trx_saved.nombre_beneficiario
    assert transaction.nombre_ordenante == trx_saved.nombre_ordenante
    assert transaction.cuenta_ordenante == trx_saved.cuenta_ordenante
    assert transaction.rfc_curp_ordenante == trx_saved.rfc_curp_ordenante
    assert transaction.speid_id == trx_saved.speid_id
    assert len(trx_saved.events) == 6
    transaction.delete()


def test_transaction_stp_input():
    data = dict(
        Clave=2456304,
        FechaOperacion=20180618,
        InstitucionOrdenante=40012,
        InstitucionBeneficiaria=90646,
        ClaveRastreo="PRUEBATAMIZI1",
        Monto=100.0,
        NombreOrdenante="BANCO",
        TipoCuentaOrdenante=40,
        CuentaOrdenante="846180000500000008",
        RFCCurpOrdenante="ND",
        NombreBeneficiario="TAMIZI",
        TipoCuentaBeneficiario=40,
        CuentaBeneficiario="646180157000000004",
        RFCCurpBeneficiario="ND",
        ConceptoPago="PRUEBA",
        ReferenciaNumerica=2423,
        Empresa="TAMIZI",
    )
    input = StpTransaction(**data)
    transaction = input.transform()
    transaction.save()
    trx_saved = Transaction.objects.get(id=transaction.id)
    assert trx_saved.stp_id == input.Clave
    assert trx_saved.monto == input.Monto * 100
    assert trx_saved.speid_id is not None
    transaction.delete()


def test_transaction_stp_input_value_error():
    data = dict(
        Clave="Clabe",
        FechaOperacion=20180618,
        InstitucionOrdenante=40012,
        InstitucionBeneficiaria=90646,
        ClaveRastreo="PRUEBATAMIZI1",
        Monto=100.0,
        NombreOrdenante="BANCO",
        TipoCuentaOrdenante=40,
        CuentaOrdenante="846180000500000008",
        RFCCurpOrdenante="ND",
        NombreBeneficiario="TAMIZI",
        TipoCuentaBeneficiario=40,
        CuentaBeneficiario="646180157000000004",
        RFCCurpBeneficiario="ND",
        ConceptoPago="PRUEBA",
        ReferenciaNumerica=2423,
        Empresa="TAMIZI",
    )
    with pytest.raises(ValidationError):
        StpTransaction(**data)


def test_transaction_speid_input():
    order = dict(
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
        version=1,
    )
    input = SpeidTransaction(**order)
    transaction = input.transform()
    transaction.save()
    trx_saved = Transaction.objects.get(id=transaction.id)
    assert trx_saved.estado == Estado.submitted
    assert trx_saved.monto == input.monto
    assert trx_saved.speid_id == input.speid_id
    transaction.delete()


def test_transaction_speid_input_validation_error():
    order = dict(
        concepto_pago=123,
        institucion_ordenante='646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='speid_id',
        version=1,
    )
    with pytest.raises(ValidationError):
        SpeidTransaction(**order)


def test_transaction_speid_clabe_cuenta_beneficiario():
    order = dict(
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
        version=1,
    )
    input = SpeidTransaction(**order)
    assert input.tipo_cuenta_beneficiario is TipoCuenta.clabe.value


def test_transaction_speid_card_cuenta_beneficiario():
    order = dict(
        concepto_pago='PRUEBA',
        institucion_ordenante='646',
        cuenta_beneficiario='5439240312453006',
        institucion_beneficiaria='072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='speid_id',
        version=1,
    )
    input = SpeidTransaction(**order)
    assert input.tipo_cuenta_beneficiario is TipoCuenta.card.value


def test_transaction_speid_non_valid_cuenta_beneficiario():
    order = dict(
        concepto_pago='PRUEBA',
        institucion_ordenante='646',
        cuenta_beneficiario='12345',
        institucion_beneficiaria='072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='speid_id',
        version=1,
    )
    with pytest.raises(ValueError):
        SpeidTransaction(**order)


def test_send_order():
    transaction = Transaction(
        concepto_pago='PRUEBA',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez Castillo de la Mancha S.A. de CV',
        nombre_ordenante='   Ricardo Sánchez Castillo de la Mancha S.A. de CV',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='speid_id',
        tipo_cuenta_beneficiario=40,
    )

    order = transaction.create_order()

    assert order.institucionOperante == transaction.institucion_ordenante
    assert order.institucionContraparte == transaction.institucion_beneficiaria
    assert order.monto == 10.20
    assert transaction.clave_rastreo == order.claveRastreo
    assert transaction.tipo_cuenta_beneficiario == order.tipoCuentaBeneficiario
    assert transaction.rfc_curp_beneficiario == order.rfcCurpBeneficiario
    assert transaction.referencia_numerica == order.referenciaNumerica
    assert order.nombreBeneficiario == (
        'Ricardo Sanchez Castillo de la Mancha' ' S'
    )
    assert order.nombreOrdenante == 'Ricardo Sanchez Castillo de la Mancha S'
    assert len(order.nombreBeneficiario) == 39
    assert len(order.nombreOrdenante) == 39

    transaction.delete()
