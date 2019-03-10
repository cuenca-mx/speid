
import pytest

from speid import db
from speid.daemon.tasks import execute_task
from speid.models import Transaction, Event
from speid.models.exceptions import MalformedOrderException
from speid.tables.types import State, Estado
from test.custom_vcr import my_vcr


class TestGeneral:

    def test_ping(self, app):
        res = app.get('/')
        assert res.status_code == 200

    def test_healthcheck(self, app):
        res = app.get('/healthcheck')
        assert res.status_code == 200

    @my_vcr.use_cassette('test/cassettes/test_create_order.yaml')
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
            "estado": Estado.succeeded,
            "speid_id": 'SPEI_TEST'
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

    @my_vcr.use_cassette('test/cassettes/test_create_order.yaml')
    def test_save_transaction_participante_tercero(self):
        transaction_request = {
            "Clave": 2456303,
            "FechaOperacion": 20180618,
            "InstitucionOrdenante": 40012,
            "InstitucionBeneficiaria": 90646,
            "ClaveRastreo": "PRUEBATAMIZI1",
            "Monto": 100.0,
            "NombreOrdenante": "BANCO",
            "TipoCuentaOrdenante": 0,
            "CuentaOrdenante": "",
            "RFCCurpOrdenante": "ND",
            "NombreBeneficiario": "TAMIZI",
            "TipoCuentaBeneficiario": 40,
            "CuentaBeneficiario": "646180157000000004",
            "RFCCurpBeneficiario": "ND",
            "ConceptoPago": "PRUEBA",
            "ReferenciaNumerica": 2423,
            "Empresa": "TAMIZI",
            "estado": Estado.succeeded,
            "speid_id": 'SPEI_TEST'
        }
        transaction = Transaction.transform(transaction_request)

        assert transaction.institucion_ordenante == 40012

    @my_vcr.use_cassette('test/cassettes/test_create_order.yaml')
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

    @my_vcr.use_cassette('test/cassettes/test_create_order.yaml')
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

    @my_vcr.use_cassette('test/cassettes/test_create_order1.yaml')
    def test_worker_with_version_0(self):
        order = dict(
            concepto_pago='PRUEBA',
            institucion_ordenante='646',
            cuenta_beneficiario='072691004495711499',
            institucion_beneficiaria='072',
            monto=1020,
            nombre_beneficiario='Pedro Sánchez',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND',
            version=0
        )
        execute_task(order)

    @my_vcr.use_cassette('test/cassettes/test_create_order.yaml')
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

    @my_vcr.use_cassette('test/cassettes/test_create_order2.yaml')
    def test_create_order_debit_card(self):
        order = dict(
            concepto_pago='DebitCardTest',
            institucion_ordenante='646',
            cuenta_beneficiario='4242424242424242',
            institucion_beneficiaria='072',
            monto=1020,
            nombre_beneficiario='Pach',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND',
            speid_id='5694433',
            version=1
        )
        execute_task(order)

    @my_vcr.use_cassette('test/cassettes/test_create_order3.yaml')
    def test_worker_with_version_1(self):
        order = dict(
            concepto_pago='PRUEBA',
            institucion_ordenante='646',
            cuenta_beneficiario='072691004495711499',
            institucion_beneficiaria='072',
            monto=1020,
            nombre_beneficiario='Pablo Sánchez',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND',
            speid_id='ANOTHER_RANDOM_ID',
            version=1
        )
        execute_task(order)

    @my_vcr.use_cassette('test/cassettes/test_create_order4.yaml')
    def test_worker_with_version_2(self):
        order = dict(
            concepto_pago='PRUEBA Version 2',
            institucion_ordenante='90646',
            cuenta_beneficiario='072691004495711499',
            institucion_beneficiaria='40072',
            monto=1020,
            nombre_beneficiario='Pablo Sánchez',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND',
            speid_id='ANOTHER_RANDOM_ID',
            version=2
        )
        execute_task(order)
