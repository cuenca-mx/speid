import datetime as dt
from typing import Optional

from pydantic import BaseModel


class TransactionStatusRequest(BaseModel):
    clave_rastreo: str
    fecha_operacion: Optional[dt.date] = None
