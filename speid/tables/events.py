from sqlalchemy import Column, ForeignKey, String

from speid import db
from speid.tables.types import State
from . import cols

events = db.Table(
    'events', db.metadata,
    cols.id('ev'), cols.created_at(),
    Column('transaction_id', String(24), ForeignKey('transactions.id')),
    Column('type', db.Enum(State)),
    Column('meta', String, nullable=False)
)
