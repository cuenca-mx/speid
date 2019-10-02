from mongoengine import (
    DateTimeField,
    Document,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)
from stpmex import Orden

from speid import STP_EMPRESA
from speid.helpers import callback_helper
from speid.types import Estado, EventType

from .events import Event
from .helpers import EnumField, date_now, mongo_to_dict, updated_at


@updated_at.apply
class Transaction(Document):
    created_at = date_now()
    updated_at = DateTimeField()
    stp_id = IntField()
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
    estado = EnumField(Estado, default=Estado.submitted)
    version = IntField()
    speid_id = StringField()
    events = ListField(ReferenceField(Event))
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
    iva = StringField()

    def to_dict(self):
        return mongo_to_dict(self, [])

    def save(
        self,
        force_insert=False,
        validate=True,
        clean=True,
        write_concern=None,
        cascade=None,
        cascade_kwargs=None,
        _refs=None,
        save_condition=None,
        signal_kwargs=None,
        **kwargs,
    ):
        if len(self.events) > 0:
            [event.save() for event in self.events]
        super().save(
            force_insert,
            validate,
            clean,
            write_concern,
            cascade,
            cascade_kwargs,
            _refs,
            save_condition,
            signal_kwargs,
            **kwargs,
        )

    def delete(self, signal_kwargs=None, **write_concern):
        if len(self.events) > 0:
            [event.delete() for event in self.events]
        super().delete(signal_kwargs, **write_concern)

    def set_state(self, state: Estado):
        self.events.append(Event(type=EventType.created))

        callback_helper.set_status_transaction(self.speid_id, state.value)
        self.estado = state

        self.events.append(Event(type=EventType.completed))

    def confirm_callback_transaction(self):
        self.events.append(Event(type=EventType.created))
        self.save()

        response = callback_helper.send_transaction(self.to_dict())
        self.estado = Estado(response['status'])

        self.events.append(
            Event(type=EventType.completed, metadata=str(response))
        )

    def get_order(self) -> Orden:
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
        for k, v in optionals.items():
            if v is None:
                k.pop(v)

        order = Orden(
            monto=self.monto / 100.0,
            conceptoPago=self.concepto_pago,
            nombreBeneficiario=self.nombre_beneficiario,
            cuentaBeneficiario=self.cuenta_beneficiario,
            institucionContraparte=self.institucion_beneficiaria,
            tipoCuentaBeneficiario=self.tipo_cuenta_beneficiario,
            nombreOrdenante=self.nombre_ordenante,
            cuentaOrdenante=self.cuenta_ordenante,
            rfcCurpOrdenante=self.rfc_curp_ordenante,
            tipoCuentaOrdenante=self.tipo_cuenta_ordenante,
            iva=self.iva,
            **optionals,
        )

        self.clave_rastreo = self.clave_rastreo or order.claveRastreo
        self.rfc_curp_beneficiario = (
            self.rfc_curp_beneficiario or order.rfcCurpBeneficiario
        )
        self.referencia_numerica = (
            self.referencia_numerica or order.referenciaNumerica
        )
        self.empresa = self.empresa or STP_EMPRESA

        return order
