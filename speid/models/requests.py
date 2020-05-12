from mongoengine import DictField, Document, StringField

from speid.types import HttpRequestMethod

from .helpers import EnumField, date_now


class Request(Document):
    created_at = date_now()
    method = EnumField(HttpRequestMethod)  # type: ignore
    path = StringField()
    query_string = StringField()
    ip_address = StringField()
    headers = DictField()
    body = StringField()
