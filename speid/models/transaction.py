import datetime as dt

from sqlalchemy.orm import relationship
from stpmex.ordenes import ORDEN_FIELDNAMES, Orden
from stpmex.types import Institucion

from speid.tables import transactions
from speid.tables.types import Estado
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
    def transform_from_order(cls, order_dict):
        trans_dict = {k: order_dict[k] for k in
                      filter(lambda r: r in order_dict,
                             transactions.columns.keys())}
        order_dict = {k: order_dict[camel_to_snake(k)]
                      for k in filter(
            lambda r: camel_to_snake(r) in order_dict, ORDEN_FIELDNAMES)}
        order = Orden(**order_dict)
        transaction = cls(**trans_dict)
        transaction.fecha_operacion = dt.date.today()
        transaction.estado = Estado.pendiente
        transaction.institucion_ordenante = order.institucionOperante
        transaction.institucion_beneficiaria = order.institucionContraparte
        transaction.clave_rastreo = order.claveRastreo
        transaction.tipo_cuenta_beneficiario = order.tipoCuentaBeneficiario
        transaction.rfc_curp_beneficiario = order.rfcCurpBeneficiario,
        transaction.concepto_pago = order.conceptoPago,
        transaction.referencia_numerica = order.referenciaNumerica,
        transaction.empresa = order.empresa,

        return transaction, order
