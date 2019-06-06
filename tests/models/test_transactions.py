import pytest
from pydantic import ValidationError

from speid.models import Transaction
from speid.types import Estado
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
