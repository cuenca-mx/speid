from stpmex_handler.tables import orden_events

from .base import db


class OrdenEvent(db.Model):
    __table__ = orden_events

    @classmethod
    def transform(cls, orden_event_dict):
        orden_event = cls(
            orden_event_id=orden_event_dict['id'],
            estado=orden_event_dict['Estado'],
            detalle=orden_event_dict['Detalle']
        )
        return orden_event
