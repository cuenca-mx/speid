import re
import uuid
from datetime import datetime
from typing import Union

from mongoengine import (
    BooleanField,
    ComplexDateTimeField,
    DateTimeField,
    DecimalField,
    DictField,
    Document,
    EmbeddedDocument,
    EmbeddedDocumentField,
    FloatField,
    IntField,
    ListField,
    signals,
)
from mongoengine.base import BaseField

_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')


def base62_encode(num):
    """
    http://stackoverflow.com/questions/1119722/base-62-conversion
    """

    alphabet = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if num == 0:
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        num, rem = divmod(num, base)
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def base62_uuid(prefix=''):
    def base62_uuid_func():
        return prefix + base62_encode(uuid.uuid1().int)

    return base62_uuid_func


def camel_to_snake(s):
    """
    https://gist.github.com/jaytaylor/3660565
    """
    subbed = _underscorer1.sub(r'\1_\2', s)
    return _underscorer2.sub(r'\1_\2', subbed).lower()


def handler(event):
    """
    http://docs.mongoengine.org/guide/signals.html?highlight=update
    Signal decorator to allow use of callback functions as class
    decorators
    """

    def decorator(fn):
        def apply(cls):
            event.connect(fn, sender=cls)
            return cls

        fn.apply = apply
        return fn

    return decorator


def date_now() -> DateTimeField:
    return DateTimeField(default=datetime.utcnow)


@handler(signals.pre_save)
def updated_at(_, document):
    document.updated_at = datetime.utcnow()


class EnumField(BaseField):
    """
    https://github.com/MongoEngine/extras-mongoengine/blob/master/
    extras_mongoengine/fields.py
    A class to register Enum type (from the package enum34) into mongo
    :param choices: must be of :class:`enum.Enum`: type
        and will be used as possible choices
    """

    def __init__(self, enum, *args, **kwargs):
        self.enum = enum
        kwargs['choices'] = [choice for choice in enum]
        super(EnumField, self).__init__(*args, **kwargs)

    def __get_value(self, enum):
        return enum.value if hasattr(enum, 'value') else enum

    def to_python(self, value):
        return self.enum(super(EnumField, self).to_python(value))

    def to_mongo(self, value):
        return self.__get_value(value)

    def prepare_query_value(self, op, value):
        return super(EnumField, self).prepare_query_value(
            op, self.__get_value(value)
        )

    def validate(self, value):
        return super(EnumField, self).validate(self.__get_value(value))

    def _validate(self, value, **kwargs):
        return super(EnumField, self)._validate(
            self.enum(self.__get_value(value)), **kwargs
        )


def mongo_to_dict(obj, exclude_fields: list = None) -> Union[dict, None]:
    """
    from: https://gist.github.com/jason-w/4969476
    """
    return_data = {}

    if obj is None:
        return None

    if isinstance(obj, Document):
        return_data['id'] = str(obj.id)

    for field_name in obj._fields:

        if field_name in exclude_fields:
            continue

        if field_name == 'id':
            continue

        data = obj._data[field_name]

        if isinstance(obj._fields[field_name], ListField):
            return_data[field_name] = list_field_to_dict(data)
        elif isinstance(obj._fields[field_name], EmbeddedDocumentField):
            return_data[field_name] = mongo_to_dict(data, [])
        elif isinstance(obj._fields[field_name], DictField):
            return_data[field_name] = data
        else:
            return_data[field_name] = mongo_to_python_type(
                obj._fields[field_name], data
            )

    return return_data


def list_field_to_dict(list_field):
    return_data = []

    for item in list_field:
        if isinstance(item, EmbeddedDocument):
            return_data.append(mongo_to_dict(item))
        else:
            return_data.append(mongo_to_python_type(item, item))

    return return_data


def mongo_to_python_type(field, data):
    rv = None
    field_type = type(field)
    if data is None:
        rv = None
    elif field_type is DateTimeField:
        rv = data.isoformat()
    elif field_type is ComplexDateTimeField:
        rv = field.to_python(data).isoformat()
    elif rv is FloatField:
        rv = float(data)
    elif field_type is IntField:
        rv = int(data)
    elif field_type is BooleanField:
        rv = bool(data)
    elif field_type is DecimalField:
        rv = data
    else:
        rv = str(data)

    return rv
