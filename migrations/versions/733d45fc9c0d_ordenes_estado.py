"""ordenes.estado

Revision ID: 733d45fc9c0d
Revises: 8cb3f92c15ef
Create Date: 2018-06-18 17:03:17.305024

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '733d45fc9c0d'
down_revision = '8cb3f92c15ef'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('ordenes', sa.Column('estado', sa.String(), nullable=False))


def downgrade():
    op.drop_column('ordenes', 'estado')
