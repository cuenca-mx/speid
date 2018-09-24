from sqlalchemy import Column, ForeignKey, Integer, String
from stpmex_handler import db
from . import cols

events = db.Table(
    'events', db.metadata,
    cols.id('ev'),
    Column('transaction_id', String(24), ForeignKey('transactions.id')),
    cols.created_at(),
    Column('type', String, nullable=False),
    Column('meta', String, nullable=False)
)
