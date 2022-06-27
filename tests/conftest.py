import datetime as dt
import os
from typing import Generator
from unittest.mock import patch

import pytest
from celery import Celery

from speid.models import Transaction
from speid.types import TipoTransaccion

SEND_TRANSACTION_TASK = os.environ['SEND_TRANSACTION_TASK']
SEND_STATUS_TRANSACTION_TASK = os.environ['SEND_STATUS_TRANSACTION_TASK']


@pytest.fixture
def mock_callback_queue():
    with patch.object(Celery, 'send_task', return_value=None):
        yield


@pytest.fixture(scope='module')
def vcr_config():
    config = dict()
    config['record_mode'] = 'none'
    return config


@pytest.fixture
def outcome_transaction() -> Generator[Transaction, None, None]:
    transaction = Transaction(
        stp_id=2456305,
        concepto_pago='PRUEBA',
        institucion_ordenante='90646',
        cuenta_beneficiario='072691004495711499',
        institucion_beneficiaria='40072',
        monto=2511,
        nombre_beneficiario='Ricardo Sánchez',
        tipo_cuenta_beneficiario=40,
        nombre_ordenante='BANCO',
        cuenta_ordenante='646180157000000004',
        rfc_curp_ordenante='ND',
        speid_id='go' + dt.datetime.now().strftime('%m%d%H%M%S'),
        version=1,
        tipo_transaccion=TipoTransaccion.retiro,
    )
    transaction.save()
    yield transaction
    transaction.delete()


@pytest.fixture
def physical_account():
    # Pongo los import aquí porque de otra forma no puedo hacer tests del
    # __init__ sin que se haya importado ya. Y así no repito el mismo fixture
    # en todos los lugares donde se usa
    from speid.models import PhysicalAccount
    from speid.types import Estado

    account = PhysicalAccount(
        estado=Estado.succeeded,
        nombre='Ricardo',
        apellido_paterno='Sánchez',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
        telefono='5567890123',
        fecha_nacimiento=dt.date(1989, 11, 25),
        pais_nacimiento='MX',
    )
    account.save()

    yield account

    account.delete()


@pytest.fixture
def moral_account():
    # Pongo los import aquí porque de otra forma no puedo hacer tests del
    # __init__ sin que se haya importado ya. Y así no repito el mismo fixture
    # en todos los lugares donde se usa
    from speid.models import MoralAccount
    from speid.types import Estado

    account = MoralAccount(
        estado=Estado.succeeded,
        nombre='Tarjetas Cuenca',
        cuenta='646180157000000004',
        rfc_curp='SACR891125HDFABC01',
        fecha_constitucion=dt.date(1989, 11, 25),
        pais='MX',
    )
    account.save()

    yield account

    account.delete()


@pytest.fixture
def orden_pago(outcome_transaction):
    return dict(
        ordenPago=dict(
            clavePago='',
            claveRastreo='CUENCA871574313626',
            conceptoPago='Dinerito',
            conceptoPago2='',
            cuentaBeneficiario='012180015025335996',
            cuentaBeneficiario2='',
            cuentaOrdenante=outcome_transaction.cuenta_ordenante,
            empresa='TAMIZI',
            estado='LQ',
            fechaOperacion='20220407',
            folioOrigen='CUENCA871574313626',
            horaServidorBanxico='18:19:25',
            idCliente='CUENCA871574313626',
            idEF=223722378,
            institucionContraparte=40012,
            institucionOperante=90646,
            medioEntrega=3,
            monto=10.0,
            nombreBeneficiario='Alex',
            nombreBeneficiario2='',
            nombreCEP='',
            nombreOrdenante=outcome_transaction.nombre_ordenante,
            prioridad=1,
            referenciaCobranza='',
            referenciaNumerica=4346435,
            rfcCEP='',
            rfcCurpBeneficiario='AAAA951020BBB',
            rfcCurpBeneficiario2='',
            rfcCurpOrdenante='AAAA951020HMCRQN00',
            sello='',
            tipoCuentaBeneficiario=40,
            tipoCuentaOrdenante=40,
            tipoPago=1,
            topologia='V',
            tsEntrega=9.155,
            urlCEP='https://www.banxico.org.mx/cep/go?i=90646',
            usuario='foo',
        )
    )
