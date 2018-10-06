from sqlalchemy import func, Column, DateTime, String

from .helpers import base62_uuid


def id(prefix):
    return Column('id', String(24), primary_key=True,
                  default=base62_uuid(prefix))


def created_at():
    return Column('created_at', DateTime(timezone=True), nullable=False,
                  default=func.now())


def updated_at():
    return Column('updated_at', DateTime(timezone=True), default=func.now(),
                  onupdate=func.now())
