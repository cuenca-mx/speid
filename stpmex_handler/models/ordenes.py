import datetime as dt

from stpmex_handler.tables import ordenes

from .base import db
from .helpers import camel_to_snake


class Orden(db.Model):
    __table__ = ordenes

    @classmethod
    def transform(cls, orden_dict):
        orden_dict = {camel_to_snake(k): v for k, v in orden_dict.items()}
        orden_dict['orden_id'] = orden_dict.pop('clave')
        orden = cls(**orden_dict)
        orden.monto = int(orden.monto * 100)
        orden.fecha_operacion = dt.datetime.strptime(
            str(orden.fecha_operacion), '%Y%m%d').date()
        return orden
