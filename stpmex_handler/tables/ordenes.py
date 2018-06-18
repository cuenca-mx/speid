from sqlalchemy import Column, Date, Integer, String

from stpmex_handler import db

from . import cols


ordenes = db.Table(
    'ordenes', db.metadata,
    cols.id('OR'), cols.created_at(),
    Column('orden_id', Integer, nullable=False),  # AKA Clave
    Column('fecha_operacion', Date, nullable=False),
    Column('institucion_ordenante', Integer, nullable=False),
    Column('institucion_beneficiaria', Integer, nullable=False),
    Column('clave_rastreo', String, nullable=False, index=True),
    Column('monto', Integer, nullable=False),
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
)
