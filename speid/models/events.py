from mongoengine import Document, StringField

from speid.types import EventType

from .helpers import date_now, EnumField


class Event(Document):
    created_at = date_now()
    type = EnumField(EventType)
    metadata = StringField()
