import pytest


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
