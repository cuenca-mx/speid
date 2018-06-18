from stpmex_handler.tables import orden_events

from .base import db


class OrdenEvent(db.Model):
    __table__ = orden_events
