import datetime
import datetime as dt

from sqlalchemy.orm import relationship

from speid.tables import transactions
from .base import db
from .events import Event
from .helpers import camel_to_snake


class Transaction(db.Model):
    __table__ = transactions

    events = relationship(Event)

    @classmethod
    def transform(cls, trans_dict):
        trans_dict = {camel_to_snake(k): v for k, v in trans_dict.items()}
        trans_dict['orden_id'] = trans_dict.pop('clave')
        trans_dict['monto'] = trans_dict['monto'] * 100
        transaction = cls(**trans_dict)
        transaction.fecha_operacion = dt.datetime.strptime(
            str(transaction.fecha_operacion),
            '%Y%m%d'
        ).date()
        return transaction

    @classmethod
    def transform_from_order(cls, order):
        transaction = cls(
            fecha_operacion=datetime.date.today(),
            institucion_ordenante=order.institucionOperante,
            institucion_beneficiaria=order.institucionContraparte,
            clave_rastreo=order.claveRastreo,
            monto=order.monto,
            nombre_ordenante=order.nombreOrdenante,
            cuenta_ordenante=order.cuentaOrdenante,
            rfc_curp_ordenante=order.rfcCurpOrdenante,
            nombre_beneficiario=order.nombreBeneficiario,
            tipo_cuenta_beneficiario=order.tipoCuentaBeneficiario,
            cuenta_beneficiario=order.cuentaBeneficiario,
            rfc_curp_beneficiario=order.rfcCurpBeneficiario,
            concepto_pago=order.conceptoPago,
            referencia_numerica=order.referenciaNumerica,
            empresa=order.empresa,
            estado="ND"
        )
        return transaction
