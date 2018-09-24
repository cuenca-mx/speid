from sqlalchemy import Column, ForeignKey, Integer, String
from speid import db
from . import cols

events = db.Table(
    'events', db.metadata,
    cols.id('ev'), cols.created_at(),
    Column('transaction_id', String(24), ForeignKey('transactions.id')),
    Column('type', String, nullable=False),
    Column('meta', String, nullable=False)
)
