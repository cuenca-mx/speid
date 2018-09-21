from stpmex_handler.models.base import db
from stpmex_handler.tables import events


class Event(db.Model):
    __table__ = events

    def __init__(self, transaction_id: int, type: str, meta: str):
        self.transaction_id = transaction_id,
        self.type = type
        self.meta = meta
