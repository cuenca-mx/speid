import pytest

from speid.models import Transaction
from speid.tasks.transactions import execute
from speid.types import Estado


@pytest.fixture
def incoming_transactions():
    yield [
        {
            'InstitucionBeneficiaria': '90646',
            'InstitucionOrdenante': '40021',
            'FechaOperacion': '20200424',
            'ClaveRastreo': 'HSBC000081',
            'Monto': 1000.0,
            'NombreOrdenante': 'CARLOS JAIR  AGUILAR PEREZ',
            'TipoCuentaOrdenante': 40,
            'CuentaOrdenante': '021650040600992156',
            'RFCCurpOrdenante': 'AUPC890116DU0',
            'NombreBeneficiario': 'CARLOS JAIR CTA CUENCA',
            'TipoCuentaBeneficiario': 40,
            'CuentaBeneficiario': '646180157000000004',
            'RFCCurpBeneficiario': '',
            'ConceptoPago': 'Andy',
            'ReferenciaNumerica': 230420,
            'Empresa': 'TAMIZI',
        },
        {
            'InstitucionBeneficiaria': '90646',
            'InstitucionOrdenante': '90646',
            'FechaOperacion': '20200424',
            'ClaveRastreo': 'MIBO587683053420',
            'Monto': 850.0,
            'NombreOrdenante': 'OMAR FLORES CASTRO',
            'TipoCuentaOrdenante': 40,
            'CuentaOrdenante': '646180142500081321',
            'RFCCurpOrdenante': 'FOCO9810191K9',
            'NombreBeneficiario': 'Omar Flores Castro',
            'TipoCuentaBeneficiario': 40,
            'CuentaBeneficiario': '646180157055148681',
            'RFCCurpBeneficiario': 'ND',
            'ConceptoPago': 'omar prro',
            'ReferenciaNumerica': 3053420,
            'Empresa': 'TAMIZI',
        },
    ]

    Transaction.objects.delete()


@pytest.mark.vcr
def test_transaction_not_in_speid(incoming_transactions):
    execute(incoming_transactions)

    saved_transaction = Transaction.objects.get(
        clave_rastreo=incoming_transactions[0]['ClaveRastreo']
    )
    assert saved_transaction.estado == Estado.succeeded


@pytest.mark.vcr
def test_transaction_not_in_backend_but_in_speid(incoming_transactions):

    execute(incoming_transactions)

    saved_transaction = Transaction.objects.get(
        clave_rastreo=incoming_transactions[0]['ClaveRastreo']
    )

    assert saved_transaction.estado == Estado.succeeded
    saved_transaction.estado = Estado.error
    saved_transaction.save()

    execute([incoming_transactions[0]])

    sent_transaction = Transaction.objects.get(
        clave_rastreo=saved_transaction.clave_rastreo
    )

    assert sent_transaction.estado == Estado.succeeded
