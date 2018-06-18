"""ordenes

Revision ID: 8cb3f92c15ef
Revises: e42eec1f5e67
Create Date: 2018-06-18 16:50:23.386519

"""
import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = '8cb3f92c15ef'
down_revision = 'e42eec1f5e67'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'ordenes',
        sa.Column('id', sa.String(length=24), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('orden_id', sa.Integer(), nullable=False),
        sa.Column('fecha_operacion', sa.Date(), nullable=False),
        sa.Column('institucion_ordenante', sa.Integer(), nullable=False),
        sa.Column('institucion_beneficiaria', sa.Integer(), nullable=False),
        sa.Column('clave_rastreo', sa.String(), nullable=False),
        sa.Column('monto', sa.Integer(), nullable=False),
        sa.Column('nombre_ordenante', sa.String(), nullable=False),
        sa.Column('tipo_cuenta_ordenante', sa.Integer(), nullable=True),
        sa.Column('cuenta_ordenante', sa.String(length=18), nullable=False),
        sa.Column('rfc_curp_ordenante', sa.String(), nullable=False),
        sa.Column('nombre_beneficiario', sa.String(), nullable=False),
        sa.Column('tipo_cuenta_beneficiario', sa.Integer(), nullable=False),
        sa.Column('cuenta_beneficiario', sa.String(length=18), nullable=False),
        sa.Column('rfc_curp_beneficiario', sa.String(), nullable=False),
        sa.Column('concepto_pago', sa.String(), nullable=False),
        sa.Column('referencia_numerica', sa.Integer(), nullable=False),
        sa.Column('empresa', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ordenes_clave_rastreo'), 'ordenes',
                    ['clave_rastreo'], unique=False)


def downgrade():
    op.drop_table('ordenes')
