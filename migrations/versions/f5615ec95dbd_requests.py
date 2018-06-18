"""requests

Revision ID: f5615ec95dbd
Revises:
Create Date: 2018-06-18 07:36:49.983878

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = 'f5615ec95dbd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'requests',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('method', sa.Enum('get', 'post', name='http_request_method'),
                  nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('path', sa.String(length=256), nullable=False),
        sa.Column('query_string', sa.String(length=1024), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=False),
        sa.Column('headers', sa.JSON(), nullable=True),
        sa.Column('body', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('requests')
