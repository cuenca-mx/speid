"""stpmex => speid

Revision ID: 447a38e07c4e
Revises: 733d45fc9c0d
Create Date: 2018-09-24 11:21:35.313030

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '447a38e07c4e'
down_revision = '733d45fc9c0d'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    op.rename_table('ordenes', 'transactions')
    op.create_table(
        'events',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('transaction_id', sa.String(length=24), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('meta', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('orden_events')
    op.alter_column('transactions', 'orden_id', nullable=True)  # make nullable
    conn.execute(text("""
        ALTER INDEX ix_ordenes_clave_rastreo RENAME TO
            ix_transactions_clave_rastreo"""))


def downgrade():
    conn = op.get_bind()
    conn.execute(text("""
        ALTER INDEX ix_transactions_clave_rastreo TO
        ix_ordenes_clave_rastreo"""))
    op.alter_column('transactions', 'orden_id', nullable=False)
    op.create_table(
        'orden_events',
        sa.Column('id', sa.VARCHAR(length=24), autoincrement=False,
                  nullable=False),
        sa.Column('created_at', sa.DateTime(), autoincrement=False,
                  nullable=False),
        sa.Column('orden_id', sa.INTEGER(), autoincrement=False,
                  nullable=False),
        sa.Column('estado', sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column('detalle', sa.INTEGER(), autoincrement=False,
                  nullable=False),
        sa.PrimaryKeyConstraint('id', name='orden_events_pkey')
    )
    op.create_index('ix_orden_events_orden_id', 'orden_events', ['orden_id'])
    op.create_index('ix_orden_events_estado', 'orden_events', ['estado'])
    op.create_index('ix_orden_events_detalle', 'orden_events', ['detalle'])
    op.drop_table('events')
    op.rename_table('transactions', 'ordenes')
