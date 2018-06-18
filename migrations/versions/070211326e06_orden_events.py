"""orden_events

Revision ID: 070211326e06
Revises: f5615ec95dbd
Create Date: 2018-06-18 10:58:18.278312

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '070211326e06'
down_revision = 'f5615ec95dbd'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'orden_events',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('orden_id', sa.Integer(), nullable=False),
        sa.Column('estado', sa.String(), nullable=False),
        sa.Column('detalle', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_orden_events_detalle'), 'orden_events',
                    ['detalle'], unique=False)
    op.create_index(op.f('ix_orden_events_estado'), 'orden_events',
                    ['estado'], unique=False)
    op.create_index(op.f('ix_orden_events_orden_id'), 'orden_events',
                    ['orden_id'], unique=False)


def downgrade():
    op.drop_table('orden_events')
