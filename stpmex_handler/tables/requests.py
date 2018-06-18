from sqlalchemy import Column, Enum, Integer, JSON, String

from stpmex_handler import db

from . import cols
from .types import HttpRequestMethod


requests = db.Table(
    'requests', db.metadata,
    cols.id('RQ'), cols.created_at(),
    Column('method', Enum(HttpRequestMethod, name='http_request_method'),
           nullable=False),
    Column('status_code', Integer, nullable=False),
    Column('path', String(256), nullable=False),
    Column('query_string', String(1024)),
    Column('ip_address', String(45), nullable=False),
    Column('headers', JSON),
    Column('body', String)
)
