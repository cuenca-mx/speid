import os
from typing import Dict, Optional

from mongoengine import NotUniqueError
from sentry_sdk import capture_exception, capture_message

from speid.models import Transaction
from speid.models.events import Event
from speid.types import Estado, EventType
from speid.validations import StpTransaction

CLABES_BLOCKED = os.getenv('CLABES_BLOCKED', '')


def process_incoming_transaction(
    incoming_transaction: dict, event_type: Optional[EventType] = None
) -> dict:
    transaction = Transaction()
    try:
        external_tx = StpTransaction(**incoming_transaction)  # type: ignore
        transaction = external_tx.transform()
        if CLABES_BLOCKED:
            clabes = CLABES_BLOCKED.split(',')
            if transaction.cuenta_beneficiario in clabes or (
                transaction.cuenta_ordenante in clabes
            ):
                capture_message('Transacción retenida')
                raise Exception
        transaction.estado = Estado.succeeded
        if not transaction.is_valid_account():
            transaction.estado = Estado.rejected
        if event_type:
            transaction.events.append(Event(type=event_type))
        transaction.confirm_callback_transaction()
        transaction.save()
        r = incoming_transaction
        r['estado'] = Estado.convert_to_stp_state(transaction.estado)
    except (NotUniqueError, TypeError) as e:
        r = dict(estado='LIQUIDACION')
        capture_exception(e)
    except Exception as e:
        r = dict(estado='LIQUIDACION')
        transaction.estado = Estado.error
        transaction.events.append(Event(type=EventType.error, metadata=str(e)))
        transaction.save()
        capture_exception(e)
    return r


def stp_model_to_dict(model) -> Dict:
    return dict(
        Clave=model.idEF,
        FechaOperacion=model.fechaOperacion.strftime('%Y%m%d'),
        InstitucionOrdenante=model.institucionContraparte,
        InstitucionBeneficiaria=model.institucionOperante,
        ClaveRastreo=model.claveRastreo,
        Monto=model.monto,
        NombreOrdenante=model.nombreOrdenante,
        TipoCuentaOrdenante=model.tipoCuentaOrdenante,
        CuentaOrdenante=model.cuentaOrdenante,
        RFCCurpOrdenante=model.rfcCurpOrdenante,
        NombreBeneficiario=model.nombreBeneficiario,
        TipoCuentaBeneficiario=model.tipoCuentaBeneficiario,
        CuentaBeneficiario=model.cuentaBeneficiario,
        RFCCurpBeneficiario=getattr(model, 'rfcCurpBeneficiario', 'NA'),
        ConceptoPago=model.conceptoPago,
        ReferenciaNumerica=model.referenciaNumerica,
        Empresa=model.empresa,
    )
