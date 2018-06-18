from sqlalchemy import Column, Integer, String

from stpmex_handler import db

from . import cols


orden_events = db.Table(
    'orden_events', db.metadata,
    cols.id('OE'), cols.created_at(),
    Column('orden_id', Integer, nullable=False, index=True),
    Column('estado', String, nullable=False, index=True),
    Column('detalle', Integer, nullable=False, index=True)
)
