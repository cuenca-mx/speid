from speid.models.base import db
from speid.tables import events


class Event(db.Model):

    __table__ = events
