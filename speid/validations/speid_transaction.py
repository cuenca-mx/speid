from pydantic import StrictStr
from pydantic.dataclasses import dataclass
from stpmex.types import TipoCuenta

from speid.models import Transaction
from speid.types import Estado


@dataclass
class SpeidTransaction:
    concepto_pago: StrictStr
    institucion_ordenante: StrictStr
    cuenta_beneficiario: StrictStr
    institucion_beneficiaria: StrictStr
    monto: int
    nombre_beneficiario: StrictStr
    nombre_ordenante: StrictStr
    cuenta_ordenante: StrictStr
    rfc_curp_ordenante: StrictStr
    speid_id: StrictStr
    version: str
    empresa: str = None
    folio_origen: str = None
    clave_rastreo: str = None
    tipo_pago: int = 1
    tipo_cuenta_ordenante: str = None
    tipo_cuenta_beneficiario: int = 40
    rfc_curp_beneficiario: str = "ND"
    email_beneficiario: str = None
    tipo_cuenta_beneficiario2: str = None
    nombre_beneficiario2: str = None
    cuenta_beneficiario2: str = None
    rfc_curpBeneficiario2: str = None
    concepto_pago2: str = None
    clave_cat_usuario1: str = None
    clave_cat_usuario2: str = None
    clave_pago: str = None
    referencia_cobranza: str = None
    referencia_numerica: int = None
    tipo_operacion: str = None
    topologia: str = "T"
    usuario: str = None
    medio_entrega: int = 3
    prioridad: int = 1
    iva: str = None

    def to_dict(self):
        return {
            k: v for k, v in self.__dict__.items() if not k.startswith('_')
        }

    def __post_init__(self):
        cuenta_len = len(self.cuenta_beneficiario)
        if cuenta_len == 18:
            self.tipo_cuenta_beneficiario = TipoCuenta.clabe.value
        elif cuenta_len in {15, 16}:
            self.tipo_cuenta_beneficiario = TipoCuenta.card.value
        else:
            raise ValueError(f'{cuenta_len} is not a valid cuenta length')

    def transform(self):
        transaction = Transaction(**self.to_dict())
        transaction.estado = Estado.submitted
        return transaction
