import datetime

from mongoengine import Document, StringField

from speid.types import EventType

from .helpers import EnumField, date_now


class Event(Document):
    created_at: datetime.datetime = date_now()
    type = EnumField(EventType)  # type: ignore
    metadata = StringField()
