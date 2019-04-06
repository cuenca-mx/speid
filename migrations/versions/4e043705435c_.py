"""empty message

Revision ID: 4e043705435c
Revises: 2773ca239148
Create Date: 2019-04-06 01:00:59.333771

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '4e043705435c'
down_revision = '2773ca239148'
branch_labels = None
depends_on = None


def upgrade():

    op.drop_constraint(
        'transactions_orden_id_key', 'transactions', type_='unique')


def downgrade():

    op.create_unique_constraint(
        'transactions_orden_id_key', 'transactions', ['orden_id'])
