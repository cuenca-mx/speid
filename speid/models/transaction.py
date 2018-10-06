import datetime as dt

from sqlalchemy.orm import relationship
from stpmex.ordenes import ORDEN_FIELDNAMES
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
        transaction = cls(**trans_dict)
        transaction.fecha_operacion = dt.date.today()
        transaction.estado = Estado.pendiente
        transaction.institucion_ordenante = \
            order_dict['institucion_contraparte']
        transaction.institucion_beneficiaria = \
            order_dict['institucion_contraparte']
        transaction.clave_rastreo = 'T'
        transaction.tipo_cuenta_beneficiario = 1
        transaction.rfc_curp_beneficiario = 'ND',
        transaction.concepto_pago = 'RO',
        transaction.referencia_numerica = 123,
        transaction.empresa = 'CO',
        order_dict = {k: order_dict[camel_to_snake(k)]
                      for k in filter(
            lambda r: camel_to_snake(r) in order_dict, ORDEN_FIELDNAMES)}
        return transaction, order_dict
