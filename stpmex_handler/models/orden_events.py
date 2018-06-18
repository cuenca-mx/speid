from stpmex_handler.tables import orden_events

from .base import db


class OrdenEvent(db.Model):
    __table__ = orden_events

    @classmethod
    def transform(cls, orden_dict):
        orden = cls(
            orden_id=orden_dict['id'],
            estado=orden_dict['estado'],
            detalle=orden_dict['detalle']
        )
        return orden
