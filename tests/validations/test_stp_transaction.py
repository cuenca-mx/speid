from speid.validations import StpTransaction


def test_converts_float_amount_to_int_correctly() -> None:
    stp_transaction = StpTransaction(
        Clave=123,
        FechaOperacion=20200320,
        InstitucionOrdenante='40106',
        InstitucionBeneficiaria='90646',
        ClaveRastreo='abc123',
        Monto=265.65,
        NombreOrdenante='Frida Kahlo',
        TipoCuentaOrdenante=40,
        CuentaOrdenante='11111',
        RFCCurpOrdenante='ABCD123456',
        NombreBeneficiario='Diego Rivera',
        TipoCuentaBeneficiario=40,
        CuentaBeneficiario='99999',
        RFCCurpBeneficiario='ND',
        ConceptoPago='AAAA',
        ReferenciaNumerica=1,
        Empresa='baz',
    )
    transaction = stp_transaction.transform()
    assert transaction.monto == 26565


def test_new_request_stp() -> None:
    request = {
        "Clave": 17658976,
        "ClaveRastreo": "2020041640014BMOV0000494354990",
        "CuentaOrdenante": "014180567802222244",
        "FechaOperacion": 20200416,
        "InstitucionBeneficiaria": 90646,
        "InstitucionOrdenante": 40014,
        "Monto": 500,
        "NombreOrdenante": "SARAHI SANCHEZ HERNANDEZ",
        "RFCCurpOrdenante": "SAHS95022114A",
        "TipoCuentaOrdenante": 40,
    }
    external_transaction = StpTransaction(**request)
    assert external_transaction
