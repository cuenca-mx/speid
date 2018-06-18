"""remove requests.status_code

Revision ID: e42eec1f5e67
Revises: 070211326e06
Create Date: 2018-06-18 11:41:41.763057

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'e42eec1f5e67'
down_revision = '070211326e06'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('requests', 'status_code')


def downgrade():
    op.add_column('requests', sa.Column(
        'status_code', sa.Integer, nullable=False))
