import datetime as dt
import re
from typing import Optional

from pydantic import ValidationError, validator
from pydantic.dataclasses import dataclass

from speid.models import Account as Model
from speid.types import Estado

CURP_RE = re.compile(r'^[A-Z]{4}[0-9]{6}[A-Z]{6}[A-Z|0-9][0-9]$')


@dataclass
class Account:
    nombre: str
    apellido_paterno: str
    cuenta: str
    rfc_curp: str
    fecha_nacimiento: dt.datetime
    pais_nacimiento: str

    telefono: Optional[str] = None
    apellido_materno: Optional[str] = None
    genero: Optional[str] = None
    entidad_federativa: Optional[str] = None
    actividad_economica: Optional[str] = None
    calle: Optional[str] = None
    numero_exterior: Optional[str] = None
    numero_interior: Optional[str] = None
    colonia: Optional[str] = None
    alcaldia_municipio: Optional[str] = None
    cp: Optional[str] = None
    email: Optional[str] = None
    id_identificacion: Optional[str] = None

    @validator('rfc_curp')
    def validate_curp_regex(cls, v) -> str:
        if (len(v) == 18 and re.match(CURP_RE, v)) or (  # CURP
            len(v) == 12 or len(v) == 13  # RFC
        ):
            return v
        raise ValidationError(errors=['Invalid curp format'], model=Model)

    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith('_')
        }

    def transform(self) -> Model:
        account = Model(**self.to_dict())
        account.estado = Estado.created
        if not account.apellido_materno:
            account.pais_nacimiento = 'SE_DESCONOCE'
            # Suggestion of stp ticket
            # https://stpmex.zendesk.com/hc/es/requests/74131
        return account
