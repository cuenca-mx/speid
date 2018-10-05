import json
import threading
import urllib.request

from speid import db
from speid.models import Transaction, Event
from speid.tables.types import State, Estado


class SendOrderEvent(threading.Thread):
    def run(self):
        body = {'id': "5623859", 'Estado': 'LIQUIDACION', 'Detalle': '0'}

        url = "http://localhost:3000/orden_events"
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json; charset=utf-8')
        json_data = json.dumps(body)
        json_data_as_bytes = json_data.encode('utf-8')
        req.add_header('Content-Length', len(json_data_as_bytes))
        response = urllib.request.urlopen(req, json_data_as_bytes)
        assert response.code == 200


class TestGeneral:

    def test_ping(self, app):
        res = app.get('/')
        assert res.status_code == 200

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

    def test_multiple_request(self):

        threads = []
        for r in range(30):
            t = SendOrderEvent()
            t.start()
            threads.append(t)

        for r in threads:
            r.join()
