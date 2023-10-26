import datetime as dt

from clabe import Clabe
from pydantic import BaseModel


class DepositStatusQuery(BaseModel):
    clave_rastreo: str
    cuenta_beneficiario: Clabe
    fecha_deposito: dt.date
