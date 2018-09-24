import datetime as dt
from speid.tables import transactions
from speid.models.base import db
from speid.models.helpers import camel_to_snake
from sqlalchemy.orm import relationship
from .events import Event


class Transaction(db.Model):
    __table__ = transactions
    events = relationship(Event,
                          primaryjoin=Event.transaction_id == __table__.c.id)

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
