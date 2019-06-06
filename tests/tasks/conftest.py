import pytest


@pytest.fixture
def default_internal_request():
    return dict(
        concepto_pago='PRUEBA',
        institucion_ordenante='646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='072',
        monto=1020,
        nombre_beneficiario='Ricardo Sánchez',
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        version=2,
    )
