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
        transaction = cls(**trans_dict)
        transaction.fecha_operacion = dt.datetime.strptime(
            str(transaction.fecha_operacion),
            '%Y%m%d'
        ).date()
        return transaction
