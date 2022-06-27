import re
from datetime import datetime
from typing import Optional

from pydantic import StrictStr
from pydantic.dataclasses import dataclass

from speid.models import Transaction
from speid.models.helpers import base62_uuid, camel_to_snake
from speid.types import TipoTransaccion

regex = re.compile(r'^[A-Z]{4}[0-9]{6}[A-Z]{6}[A-Z|0-9][0-9]$')


@dataclass
class StpTransaction:
    FechaOperacion: int
    InstitucionOrdenante: str
    InstitucionBeneficiaria: str
    ClaveRastreo: StrictStr
    Monto: float
    NombreOrdenante: StrictStr
    TipoCuentaOrdenante: int
    CuentaOrdenante: StrictStr
    RFCCurpOrdenante: StrictStr
    NombreBeneficiario: StrictStr
    TipoCuentaBeneficiario: int
    CuentaBeneficiario: StrictStr
    RFCCurpBeneficiario: StrictStr
    ConceptoPago: StrictStr
    ReferenciaNumerica: int
    Empresa: StrictStr
    Clave: Optional[int] = None

    def transform(self) -> Transaction:
        trans_dict = {
            camel_to_snake(k): v
            for k, v in self.__dict__.items()
            if not k.startswith('_')
        }
        trans_dict['stp_id'] = trans_dict.pop('clave', None)
        trans_dict['monto'] = round(trans_dict['monto'] * 100)
        trans_dict['tipo'] = TipoTransaccion.deposito
        transaction = Transaction(**trans_dict)
        transaction.speid_id = base62_uuid('SR')()
        transaction.fecha_operacion = datetime.strptime(
            str(transaction.fecha_operacion), '%Y%m%d'
        ).date()

        (
            transaction.rfc_ordenante,
            transaction.curp_ordenante,
        ) = self.get_rfc_curp()
        return transaction

    def get_rfc_curp(self):
        curp = None
        rfc = None
        if regex.match(self.RFCCurpOrdenante):
            curp = self.RFCCurpOrdenante
        elif len(self.RFCCurpOrdenante) == 13:
            rfc = self.RFCCurpOrdenante
        return rfc, curp
