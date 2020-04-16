from datetime import datetime
from typing import Optional

from pydantic import StrictStr
from pydantic.dataclasses import dataclass

from speid.models import Transaction
from speid.models.helpers import base62_uuid, camel_to_snake


@dataclass
class StpTransaction:
    Clave: int
    FechaOperacion: int
    InstitucionOrdenante: str
    InstitucionBeneficiaria: str
    ClaveRastreo: StrictStr
    Monto: float
    NombreOrdenante: StrictStr
    TipoCuentaOrdenante: int
    CuentaOrdenante: StrictStr
    RFCCurpOrdenante: StrictStr
    NombreBeneficiario: Optional[str] = ''
    TipoCuentaBeneficiario: Optional[int] = None
    CuentaBeneficiario: Optional[str] = ''
    RFCCurpBeneficiario: Optional[str] = ''
    ConceptoPago: Optional[str] = ''
    ReferenciaNumerica: Optional[int] = None
    Empresa: Optional[str] = ''

    def transform(self) -> Transaction:
        trans_dict = {
            camel_to_snake(k): v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
        trans_dict['stp_id'] = trans_dict.pop('clave')
        trans_dict['monto'] = round(trans_dict['monto'] * 100)
        transaction = Transaction(**trans_dict)
        transaction.speid_id = base62_uuid('SR')()
        transaction.fecha_operacion = datetime.strptime(
            str(transaction.fecha_operacion), '%Y%m%d'
        ).date()
        return transaction
