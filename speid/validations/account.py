import datetime as dt
import re
from typing import Optional

from clabe import Clabe
from pydantic import ValidationError, validator
from pydantic.dataclasses import dataclass
from stpmex.types import EntidadFederativa

from speid.models import Account as AccountModel
from speid.models import MoralAccount as MoralAccountModel
from speid.models import PhysicalAccount as PhysicalAccountModel
from speid.types import Estado

CURP_RE = re.compile(r'^[A-Z]{4}[0-9]{6}[A-Z]{6}[A-Z|0-9][0-9]$')


@dataclass
class Account:
    nombre: str
    rfc_curp: str
    cuenta: Clabe

    @validator('rfc_curp')
    def validate_curp_regex(cls, v) -> str:
        if (len(v) == 18 and re.match(CURP_RE, v)) or (  # CURP
            len(v) == 12 or len(v) == 13  # RFC
        ):
            return v
        raise ValidationError(
            errors=['Invalid curp format'], model=AccountModel
        )

    def to_dict(self) -> dict:
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith('_')
        }


@dataclass
class PhysicalAccount(Account):
    apellido_paterno: str
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

    def transform(self) -> AccountModel:
        account = PhysicalAccountModel(**self.to_dict())
        account.estado = Estado.created
        if not account.apellido_materno:
            account.pais_nacimiento = 'SE_DESCONOCE'
            # Suggestion of stp ticket
            # https://stpmex.zendesk.com/hc/es/requests/74131
        return account


@dataclass
class MoralAccount(Account):
    pais: str
    fecha_constitucion: dt.datetime

    entidad_federativa: Optional[str] = None
    actividad_economica: Optional[str] = None

    is_restricted: Optional[bool] = False
    allowed_curp: Optional[str] = None
    allowed_rfc: Optional[str] = None

    def transform(self) -> AccountModel:
        data = self.to_dict()
        data['is_restricted'] = (
            self.allowed_curp is not None or self.allowed_rfc is not None
        )
        try:
            data['entidad_federativa'] = EntidadFederativa[
                data['entidad_federativa']
            ]
        except KeyError:
            ...

        account = MoralAccountModel(**data)
        return account
