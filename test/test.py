from speid import db
from speid.models import Transaction, Event
from speid.tables.types import State, Estado


class TestGeneral:

    def test_save_transaction(self):
        transaction_request = {
            "Clave": 2456303,
            "FechaOperacion": 20180618,
            "InstitucionOrdenante": 846,
            "InstitucionBeneficiaria": 90646,
            "ClaveRastreo": "PRUEBATAMIZI1",
            "Monto": 100.0,
            "NombreOrdenante": "BANCO",
            "TipoCuentaOrdenante": 40,
            "CuentaOrdenante": "846180000500000008",
            "RFCCurpOrdenante": "ND",
            "NombreBeneficiario": "TAMIZI",
            "TipoCuentaBeneficiario": 40,
            "CuentaBeneficiario": "646180157000000004",
            "RFCCurpBeneficiario": "ND",
            "ConceptoPago": "PRUEBA",
            "ReferenciaNumerica": 2423,
            "Empresa": "TAMIZI",
            "estado": Estado.pendiente
        }
        transaction = Transaction.transform(transaction_request)
        db.session.add(transaction)
        db.session.commit()
        event = Event(
            transaction_id=transaction.id,
            type=State.created,
            meta='TEST'
        )
        db.session.add(event)
        db.session.commit()
        assert transaction.id is not None
        assert event.id is not None
