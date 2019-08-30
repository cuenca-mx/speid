from mongoengine import Document, StringField

from speid.types import EventType

from .helpers import EnumField, date_now


class Event(Document):
    created_at = date_now()
    type = EnumField(EventType)
    metadata = StringField()
