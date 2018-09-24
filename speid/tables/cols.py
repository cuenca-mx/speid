from sqlalchemy import func, Column, DateTime, String

from .helpers import base62_uuid


def id(prefix):
    return Column('id', String(24), primary_key=True,
                  default=base62_uuid(prefix))


def created_at():
    return Column('created_at', DateTime, nullable=False,
                  default=func.now())
