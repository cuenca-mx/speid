from sqlalchemy import Column, ForeignKey, String, Enum

from speid import db
from speid.tables.types import State
from . import cols

events = db.Table(
    'events',
    cols.id('ev'), cols.created_at(),
    Column('transaction_id', String(24), ForeignKey('transactions.id')),
    Column('type', Enum(State, name='event_type'), nullable=False),
    Column('meta', String, nullable=False)
)
