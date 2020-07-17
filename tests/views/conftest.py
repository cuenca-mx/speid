from datetime import datetime
from typing import Generator

import pytest

from speid import app
from speid.models import Transaction


@pytest.fixture
def client():
    app.testing = True
    client = app.test_client()
    return client


@pytest.fixture
def outcome_transaction() -> Generator[Transaction, None, None]:
    transaction = Transaction(
        stp_id=2456305,
        concepto_pago='PRUEBA',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=2511,
        nombre_beneficiario='Ricardo Sánchez',
        tipo_cuenta_beneficiario=40,
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='go' + datetime.now().strftime('%m%d%H%M%S'),
        version=1,
    )
    transaction.save()
    yield transaction
    transaction.delete()


@pytest.fixture
def default_blocked_transaction():
    return dict(
        Clave=2456304,
        FechaOperacion=20180618,
        InstitucionOrdenante=40012,
        InstitucionBeneficiaria=90646,
        ClaveRastreo="PRUEBABloqueo",
        Monto=100.0,
        NombreOrdenante="BANCO",
        TipoCuentaOrdenante=40,
        CuentaOrdenante="846180000500000009",
        RFCCurpOrdenante="ND",
        NombreBeneficiario="TAMIZI",
        TipoCuentaBeneficiario=40,
        CuentaBeneficiario="646180157000000666",
        RFCCurpBeneficiario="ND",
        ConceptoPago="PRUEBA BLOQUEO",
        ReferenciaNumerica=2423,
        Empresa="TAMIZI",
    )


@pytest.fixture
def default_blocked_incoming_transaction():
    return dict(
        Clave=24569304,
        FechaOperacion=20180618,
        InstitucionOrdenante=40012,
        InstitucionBeneficiaria=90646,
        ClaveRastreo="PRUEBABloqueo",
        Monto=100.0,
        NombreOrdenante="BANCO",
        TipoCuentaOrdenante=40,
        CuentaOrdenante="846180000500000109",
        RFCCurpOrdenante="ND",
        NombreBeneficiario="TAMIZI",
        TipoCuentaBeneficiario=40,
        CuentaBeneficiario="646180157000000667",
        RFCCurpBeneficiario="ND",
        ConceptoPago="PRUEBA BLOQUEO",
        ReferenciaNumerica=2423,
        Empresa="TAMIZI",
    )


@pytest.fixture
def default_income_transaction():
    return dict(
        Clave=2456303,
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
