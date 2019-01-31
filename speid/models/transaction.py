import datetime as dt

from sqlalchemy.orm import relationship
from stpmex.ordenes import ORDEN_FIELDNAMES, Orden
from stpmex.types import AccountType

import clabe
import luhnmod10

from speid.tables import transactions
from speid.tables.types import Estado
from speid.tables.helpers import base62_uuid

from .base import db
from .events import Event
from .helpers import camel_to_snake


def contain_required_fields(required_fields, dict_val):
    for r in required_fields:
        if r not in dict_val:
            return False
    return True


class TransactionFactory:

    @classmethod
    def create_transaction(cls, version, order_dict):
        if version == 0 and Transaction.is_valid(order_dict):
            return Transaction.transform_from_order(order_dict)
        if version == 1 and TransactionV1.is_valid(order_dict):
            return TransactionV1.transform_from_order(order_dict)
        if version == 2 and TransactionV2.is_valid(order_dict):
            return TransactionV2.transform_from_order(order_dict)
        return Transaction.error(order_dict)


class Transaction(db.Model):
    __table__ = transactions

    events = relationship(Event)

    required_fields = [
        "concepto_pago",
        "institucion_ordenante",
        "cuenta_beneficiario",
        "institucion_beneficiaria",
        "monto",
        "nombre_beneficiario",
        "nombre_ordenante",
        "cuenta_ordenante",
        "rfc_curp_ordenante"
    ]

    @classmethod
    def error(cls, order_dict):
        trans_dict = {camel_to_snake(k): v for k, v in order_dict.items()}
        transaction = Transaction(**trans_dict)
        transaction.estado = Estado.error
        transaction.fecha_operacion = dt.date.today()
        transaction.clave_rastreo = "ND"
        transaction.tipo_cuenta_beneficiario = 0
        transaction.rfc_curp_beneficiario = "ND",
        transaction.concepto_pago = "ND",
        transaction.referencia_numerica = 0,
        transaction.empresa = "ND"
        return transaction, None

    @classmethod
    def is_valid(cls, order_dict):
        if contain_required_fields(cls.required_fields, order_dict):
            if clabe.validate_clabe(order_dict['cuenta_beneficiario']) \
                    or luhnmod10.valid(order_dict['cuenta_beneficiario']):
                return True
        return False

    @classmethod
    def transform(cls, trans_dict):
        trans_dict = {camel_to_snake(k): v for k, v in trans_dict.items()}
        trans_dict['orden_id'] = trans_dict.pop('clave')
        trans_dict['monto'] = trans_dict['monto'] * 100
        transaction = cls(**trans_dict)
        if transaction.speid_id is None:
            transaction.speid_id = base62_uuid('SR')()
        transaction.fecha_operacion = dt.datetime.strptime(
            str(transaction.fecha_operacion),
            '%Y%m%d'
        ).date()
        return transaction

    @classmethod
    def transform_from_order(cls, order_dict):

        if len(order_dict['cuenta_beneficiario']) == 16:
            order_dict['tipo_cuenta_beneficiario'] = (
                AccountType.DEBIT_CARD.value)

        trans_dict = {k: order_dict[k] for k in
                      filter(lambda r: r in order_dict,
                             transactions.columns.keys())}
        order_dict = {k: order_dict[camel_to_snake(k)]
                      for k in filter(
            lambda r: camel_to_snake(r) in order_dict, ORDEN_FIELDNAMES)}
        order = Orden(**order_dict)
        transaction = cls(**trans_dict)
        transaction.fecha_operacion = dt.date.today()
        transaction.estado = Estado.submitted
        order.institucionOperante = clabe.BANKS[
            transaction.institucion_ordenante]
        order.institucionContraparte = clabe.BANKS[
            transaction.institucion_beneficiaria]
        transaction.clave_rastreo = order.claveRastreo
        transaction.tipo_cuenta_beneficiario = order.tipoCuentaBeneficiario
        transaction.rfc_curp_beneficiario = order.rfcCurpBeneficiario,
        transaction.concepto_pago = order.conceptoPago,
        transaction.referencia_numerica = order.referenciaNumerica,
        transaction.empresa = order.empresa,

        return transaction, order


class TransactionV1(Transaction):

    required_v1_fields = ['speid_id']

    @classmethod
    def is_valid(cls, order_dict):
        return super().is_valid(order_dict) and contain_required_fields(
            cls.required_v1_fields,
            order_dict)

    @classmethod
    def transform_from_order(cls, order_dict):
        transaction, order = super().transform_from_order(order_dict)
        transaction.speid_id = order_dict['speid_id']
        return transaction, order


class TransactionV2(Transaction):

    @classmethod
    def is_valid(cls, order_dict):
        return super().is_valid(order_dict)

    @classmethod
    def transform_from_order(cls, order_dict):
        if len(order_dict['cuenta_beneficiario']) == 16:
            order_dict['tipo_cuenta_beneficiario'] = (
                AccountType.DEBIT_CARD.value)

        trans_dict = {k: order_dict[k] for k in
                      filter(lambda r: r in order_dict,
                             transactions.columns.keys())}
        order_dict = {k: order_dict[camel_to_snake(k)]
                      for k in filter(
            lambda r: camel_to_snake(r) in order_dict, ORDEN_FIELDNAMES)}
        order = Orden(**order_dict)
        transaction = cls(**trans_dict)
        transaction.fecha_operacion = dt.date.today()
        transaction.estado = Estado.submitted
        order.institucionOperante = transaction.institucion_ordenante
        order.institucionContraparte = transaction.institucion_beneficiaria
        transaction.clave_rastreo = order.claveRastreo
        transaction.tipo_cuenta_beneficiario = order.tipoCuentaBeneficiario
        transaction.rfc_curp_beneficiario = order.rfcCurpBeneficiario,
        transaction.concepto_pago = order.conceptoPago,
        transaction.referencia_numerica = order.referenciaNumerica,
        transaction.empresa = order.empresa,

        return transaction, order
