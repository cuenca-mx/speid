import datetime as dt
from typing import Optional

from pydantic.dataclasses import dataclass

from speid.models import Account
from speid.types import Estado


@dataclass
class Account:
    nombre: str
    apellido_paterno: str
    cuenta: str
    rfcCurp: str
    telefono: str = None

    apellido_materno: Optional[str] = None
    genero: Optional[str] = None
    fecha_nacimiento: Optional[dt.datetime] = None
    entidad_federativa: Optional[str] = None
    actividad_economica: Optional[str] = None
    calle: Optional[str] = None
    numero_exterior: Optional[str] = None
    numero_interior: Optional[str] = None
    colonia: Optional[str] = None
    alcaldia_municipio: Optional[str] = None
    cp: Optional[str] = None
    pais: Optional[str] = None
    email: Optional[str] = None
    id_identificacion: Optional[str] = None

    def transform(self) -> Account:
        account = Account(**self.to_dict())
        account.estado = Estado.created
        return account
