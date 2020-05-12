from pydantic import StrictStr
from pydantic.dataclasses import dataclass

from speid.models import Transaction
from stpmex.types import TipoCuenta


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
    empresa: str = ''
    folio_origen: str = ''
    clave_rastreo: str = ''
    tipo_pago: int = 1
    tipo_cuenta_ordenante: str = ''
    tipo_cuenta_beneficiario: int = 40
    rfc_curp_beneficiario: str = "ND"
    email_beneficiario: str = ''
    tipo_cuenta_beneficiario2: str = ''
    nombre_beneficiario2: str = ''
    cuenta_beneficiario2: str = ''
    rfc_curpBeneficiario2: str = ''
    concepto_pago2: str = ''
    clave_cat_usuario1: str = ''
    clave_cat_usuario2: str = ''
    clave_pago: str = ''
    referencia_cobranza: str = ''
    referencia_numerica: int = 0
    tipo_operacion: str = ''
    topologia: str = "T"
    usuario: str = ''
    medio_entrega: int = 3
    prioridad: int = 1

    def to_dict(self) -> dict:
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

    def transform(self) -> Transaction:
        transaction = Transaction(**self.to_dict())
        return transaction
