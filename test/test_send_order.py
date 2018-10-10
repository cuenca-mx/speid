import json

import pytest
from celery import Celery
from sqlalchemy.orm.exc import NoResultFound


class TestSendOrder:

    def test_generate_order(self, app):
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
        app = Celery('speid')
        app.config_from_object('speid.daemon.celeryconfig')
        app.send_task('speid.daemon.tasks.send_order',
                      kwargs={'order_val': order})

    def test_create_order_found(self, app):
        data = dict(
            id='2456303',
            Estado='LIQUIDACION',
            Detalle="0"
        )
        res = app.post('/orden_events', data=json.dumps(data),
                       content_type='application/json')
        assert res.status_code == 200

    def test_fail_create_order(self, app):
        data = dict(
            Estado='LIQUIDACION',
            Detalle='0'
        )
        res = app.post('/orden_events', data=json.dumps(data),
                       content_type='application/json')
        assert res.status_code == 400

    def test_fail_id_create_order(self, app):
        data = dict(
            id='999999',  # An ID we don't have in the records
            Estado='LIQUIDACION',
            Detalle='0'
        )
        with pytest.raises(NoResultFound):
            app.post('/orden_events', data=json.dumps(data),
                     content_type='application/json')
