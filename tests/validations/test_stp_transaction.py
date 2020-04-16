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
