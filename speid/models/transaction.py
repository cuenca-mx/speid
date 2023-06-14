import os
from datetime import datetime
from enum import Enum
from typing import Optional

import pytz
from mongoengine import (
    DateTimeField,
    Document,
    DoesNotExist,
    IntField,
    ListField,
    ReferenceField,
    StringField,
    signals,
)
from sentry_sdk import capture_exception
from stpmex.business_days import get_next_business_day
from stpmex.exc import NoEntityFound, StpmexException
from stpmex.resources import Orden
from stpmex.types import Estado as STPEstado

from speid import STP_EMPRESA
from speid.exc import MalformedOrderException
from speid.helpers import callback_helper
from speid.processors import stpmex_client
from speid.types import Estado, EventType, TipoTransaccion

from .account import Account
from .base import BaseModel
from .events import Event
from .helpers import (
    EnumField,
    date_now,
    delete_events,
    handler,
    save_events,
    updated_at,
)

SKIP_VALIDATION_PRIOR_SEND_ORDER = (
    os.getenv('SKIP_VALIDATION_PRIOR_SEND_ORDER', 'false').lower() == 'true'
)

STP_FAILED_STATUSES = [
    STPEstado.traspaso_cancelado,
    STPEstado.cancelada,
    STPEstado.cancelada_adapter,
    STPEstado.cancelada_rechazada,
]


@handler(signals.pre_save)
def pre_save_transaction(sender, document):
    date = document.fecha_operacion or datetime.today()
    document.compound_key = (
        f'{document.clave_rastreo}:{date.strftime("%Y%m%d")}'
    )


# Min amount accepted in restricted accounts
MIN_AMOUNT = int(os.getenv('MIN_AMOUNT', '10000'))


@updated_at.apply
@save_events.apply
@pre_save_transaction.apply
@delete_events.apply
class Transaction(Document, BaseModel):
    created_at = date_now()
    updated_at = DateTimeField()
    stp_id = IntField()
    tipo: TipoTransaccion = EnumField(TipoTransaccion)
    fecha_operacion = DateTimeField()
    institucion_ordenante = StringField()
    institucion_beneficiaria = StringField()
    clave_rastreo = StringField()
    monto = IntField()
    nombre_ordenante = StringField()
    tipo_cuenta_ordenante = IntField()
    cuenta_ordenante = StringField()
    rfc_curp_ordenante = StringField()
    nombre_beneficiario = StringField()
    tipo_cuenta_beneficiario = IntField()
    cuenta_beneficiario = StringField()
    rfc_curp_beneficiario = StringField()
    concepto_pago = StringField()
    referencia_numerica = IntField()
    empresa = StringField()
    estado: Enum = EnumField(Estado, default=Estado.created)
    version = IntField()
    speid_id = StringField()
    folio_origen = StringField()
    tipo_pago = IntField()
    email_beneficiario = StringField()
    tipo_cuenta_beneficiario2 = StringField()
    nombre_beneficiario2 = StringField()
    cuenta_beneficiario2 = StringField()
    rfc_curpBeneficiario2 = StringField()
    concepto_pago2 = StringField()
    clave_cat_usuario1 = StringField()
    clave_cat_usuario2 = StringField()
    clave_pago = StringField()
    referencia_cobranza = StringField()
    tipo_operacion = StringField()
    topologia = StringField()
    usuario = StringField()
    medio_entrega = IntField()
    prioridad = IntField()
    compound_key = StringField()
    detalle = StringField()

    curp_ordenante = StringField()
    rfc_ordenante = StringField()

    events = ListField(ReferenceField(Event))

    meta = {
        'indexes': [
            '+stp_id',
            '+speid_id',
            '+clave_rastreo',
            # The Unique-Sparse index skips over any document that is missing
            # the indexed field (null values)
            {'fields': ['+compound_key'], 'unique': True, 'sparse': True},
            {
                'fields': ['+stp_id', '+tipo'],
                'partialFilterExpression': {'tipo': TipoTransaccion.retiro},
            },
        ]
    }

    def set_state(self, state: Estado):
        from ..tasks.transactions import send_transaction_status

        send_transaction_status.apply_async((str(self.id), state))
        self.estado = state

        self.events.append(Event(type=EventType.completed))

    def confirm_callback_transaction(self):
        response = ''
        self.events.append(Event(type=EventType.created))
        self.save()
        callback_helper.send_transaction(self.to_dict())

        self.events.append(
            Event(type=EventType.completed, metadata=str(response))
        )

    def is_valid_account(self) -> bool:
        is_valid = True
        try:
            account = Account.objects.get(cuenta=self.cuenta_beneficiario)
            if account.is_restricted:
                ordenante = self.rfc_curp_ordenante
                is_valid = (
                    ordenante == account.allowed_rfc
                    or ordenante == account.allowed_curp
                ) and self.monto >= MIN_AMOUNT
        except DoesNotExist:
            pass
        return is_valid

    def fetch_stp_status(self) -> Optional[STPEstado]:
        # checa status en stp
        estado = None
        try:
            stp_order = stpmex_client.ordenes.consulta_clave_rastreo(
                claveRastreo=self.clave_rastreo,
                institucionOperante=self.institucion_ordenante,
                fechaOperacion=get_next_business_day(self.created_at),
            )
            estado = stp_order.estado
        except NoEntityFound:
            ...
        return estado

    def is_current_working_day(self) -> bool:
        # checks if transaction was made in the current working day
        local = self.created_at.replace(tzinfo=pytz.utc)
        local = local.astimezone(pytz.timezone('America/Mexico_City'))
        return get_next_business_day(local) == datetime.utcnow().date()

    def fail_if_not_found_stp(self) -> None:
        # if transaction is not found in stp, or has a failed status,
        # return to origin. Only checking for curent working day
        if not self.is_current_working_day():
            return
        try:
            estado = self.fetch_stp_status()
        except StpmexException as ex:
            capture_exception(ex)
        else:
            if not estado or estado in STP_FAILED_STATUSES:
                self.set_state(Estado.failed)
                self.save()

    def create_order(self) -> Orden:
        # Validate account has already been created
        if not SKIP_VALIDATION_PRIOR_SEND_ORDER:
            try:
                account = Account.objects.get(cuenta=self.cuenta_ordenante)
                assert account.estado is Estado.succeeded
            except (DoesNotExist, AssertionError):
                self.estado = Estado.error
                self.save()
                raise MalformedOrderException(
                    f'Account has not been registered: {self.cuenta_ordenante}'
                    f', stp_id: {self.stp_id}'
                )

        # Don't send if stp_id already exists
        if self.stp_id:
            return Orden(  # type: ignore
                id=self.stp_id,
                monto=self.monto / 100.0,
                conceptoPago=self.concepto_pago,
                nombreBeneficiario=self.nombre_beneficiario,
                cuentaBeneficiario=self.cuenta_beneficiario,
                institucionContraparte=self.institucion_beneficiaria,
                cuentaOrdenante=self.cuenta_ordenante,
            )

        optionals = dict(
            institucionOperante=self.institucion_ordenante,
            claveRastreo=self.clave_rastreo,
            referenciaNumerica=self.referencia_numerica,
            rfcCurpBeneficiario=self.rfc_curp_beneficiario,
            medioEntrega=self.medio_entrega,
            prioridad=self.prioridad,
            tipoPago=self.tipo_pago,
            topologia=self.topologia,
        )
        # remove if value is None
        remove = []
        for k, v in optionals.items():
            if v is None:
                remove.append(k)
        for k in remove:
            optionals.pop(k)

        try:
            order = stpmex_client.ordenes.registra(
                monto=self.monto / 100.0,
                conceptoPago=self.concepto_pago,
                nombreBeneficiario=self.nombre_beneficiario,
                cuentaBeneficiario=self.cuenta_beneficiario,
                institucionContraparte=self.institucion_beneficiaria,
                tipoCuentaBeneficiario=self.tipo_cuenta_beneficiario,
                nombreOrdenante=self.nombre_ordenante,
                cuentaOrdenante=self.cuenta_ordenante,
                rfcCurpOrdenante=self.rfc_curp_ordenante,
                **optionals,
            )
        except (Exception) as e:  # Anything can happen here
            self.events.append(Event(type=EventType.error, metadata=str(e)))
            self.estado = Estado.error
            self.save()
            raise e
        else:
            # breakpoint()
            self.clave_rastreo = self.clave_rastreo or order.claveRastreo
            self.rfc_curp_beneficiario = (
                self.rfc_curp_beneficiario or order.rfcCurpBeneficiario
            )
            self.referencia_numerica = (
                self.referencia_numerica or order.referenciaNumerica
            )
            self.empresa = self.empresa or STP_EMPRESA
            self.stp_id = order.id

            self.events.append(
                Event(type=EventType.completed, metadata=str(order))
            )
            self.estado = Estado.submitted
            self.save()
            return order
