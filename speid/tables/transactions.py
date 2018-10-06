from sqlalchemy import Column, Date, Integer, String, CheckConstraint, Enum

from speid import db
from speid.tables.types import Estado
from . import cols

transactions = db.Table(
    'transactions',
    cols.id('tr'), cols.created_at(), cols.updated_at(),
    Column('orden_id', Integer, unique=True),  # STP Ordenes.clave
    Column('fecha_operacion', Date, nullable=False),
    Column('institucion_ordenante', Integer, nullable=False),
    Column('institucion_beneficiaria', Integer, nullable=False),
    Column('clave_rastreo', String, nullable=False, index=True),
    Column('monto', Integer, CheckConstraint('monto>0'), nullable=False),
    Column('nombre_ordenante', String, nullable=False),
    Column('tipo_cuenta_ordenante', Integer),
    Column('cuenta_ordenante', String(18), nullable=False),
    Column('rfc_curp_ordenante', String, nullable=False),
    Column('nombre_beneficiario', String, nullable=False),
    Column('tipo_cuenta_beneficiario', Integer, nullable=False),
    Column('cuenta_beneficiario', String(18), nullable=False),
    Column('rfc_curp_beneficiario', String, nullable=False),
    Column('concepto_pago', String, nullable=False),
    Column('referencia_numerica', Integer, nullable=False),
    Column('empresa', String, nullable=False),
    Column('estado', Enum(Estado)),
    Column('version', Integer, CheckConstraint('version>=0 AND version<2'))
)
