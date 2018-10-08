import pytest

from speid import db
from speid.daemon.tasks import execute_task
from speid.models import Transaction, Event
from speid.models.exceptions import MalformedOrderException
from speid.tables.types import State, Estado


class TestGeneral:

    def test_ping(self, app):
        res = app.get('/')
        assert res.status_code == 200

    def test_save_transaction(self):
        transaction_request = {
            "Clave": 2456303,
            "FechaOperacion": 20180618,
            "InstitucionOrdenante": 40012,
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
            "estado": Estado.success,
            "speid_id": "SPEI_TEST"
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

    def test_worker_with_incorrect_version(self):
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
            version=99999
        )
        with pytest.raises(MalformedOrderException):
            execute_task(order_val=order)

    def test_worker_without_version(self):
        order = dict(
            concepto_pago='PRUEBA',
            institucion_ordenante='646',
            cuenta_beneficiario='072691004495711499',
            institucion_beneficiaria='072',
            monto=1020,
            nombre_beneficiario='Ricardo Sánchez',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND'
        )
        execute_task(order)

    def test_worker_with_version_0(self):
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
            version=0
        )
        execute_task(order)

    def test_malformed_order_worker_with_version_1(self):
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
            version=1
        )
        with pytest.raises(MalformedOrderException):
            execute_task(order)

    def test_worker_with_version_1(self):
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
            speid_id='SOME_RANDOM_ID',
            version=1
        )
        execute_task(order)
