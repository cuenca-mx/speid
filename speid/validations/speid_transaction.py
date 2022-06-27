from typing import Optional

from pydantic import StrictStr
from pydantic.dataclasses import dataclass
from stpmex.types import TipoCuenta

from speid.models import Transaction
from speid.types import TipoTransaccion


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
    empresa: Optional[str] = None
    folio_origen: Optional[str] = None
    clave_rastreo: Optional[str] = None
    tipo_pago: int = 1
    tipo_cuenta_ordenante: Optional[str] = None
    tipo_cuenta_beneficiario: int = 40
    rfc_curp_beneficiario: str = "ND"
    email_beneficiario: Optional[str] = None
    tipo_cuenta_beneficiario2: Optional[str] = None
    nombre_beneficiario2: Optional[str] = None
    cuenta_beneficiario2: Optional[str] = None
    rfc_curpBeneficiario2: Optional[str] = None
    concepto_pago2: Optional[str] = None
    clave_cat_usuario1: Optional[str] = None
    clave_cat_usuario2: Optional[str] = None
    clave_pago: Optional[str] = None
    referencia_cobranza: Optional[str] = None
    referencia_numerica: Optional[int] = None
    tipo_operacion: Optional[str] = None
    topologia: str = "T"
    usuario: Optional[str] = None
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
        transaction_dict = self.to_dict()
        transaction_dict['tipo'] = TipoTransaccion.retiro
        transaction = Transaction(**transaction_dict)
        return transaction
