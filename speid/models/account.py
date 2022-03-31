from enum import Enum

from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)
from stpmex.resources import CuentaFisica, CuentaMoral
from stpmex.types import Genero, Pais

from speid.processors import stpmex_client
from speid.types import Estado, EventType

from .base import BaseModel
from .events import Event
from .helpers import (
    EnumField,
    date_now,
    delete_events,
    save_events,
    updated_at,
)


@updated_at.apply
@save_events.apply
@delete_events.apply
class Account(Document, BaseModel):
    meta = {'allow_inheritance': True}

    created_at = date_now()
    updated_at = DateTimeField()
    estado: Enum = EnumField(Estado, default=Estado.created)

    nombre = StringField()
    cuenta = StringField(unique=True)
    rfc_curp = StringField()

    # if is_restricted check ordenante_curp_rfc is
    # self.allowed_rfc o self.allowed_curp
    is_restricted = BooleanField(required=False)
    allowed_rfc = StringField(required=False)
    allowed_curp = StringField(required=False)

    events = ListField(ReferenceField(Event))


@updated_at.apply
@save_events.apply
@delete_events.apply
class PhysicalAccount(Account):
    apellido_paterno = StringField()
    apellido_materno = StringField(required=False)
    telefono = StringField()
    fecha_nacimiento = DateTimeField(required=False)
    pais_nacimiento = StringField(required=False)

    genero = EnumField(Genero, required=False)  # type: ignore
    entidad_federativa = IntField(required=False)
    actividad_economica = IntField(required=False)
    calle = StringField(required=False)
    numero_exterior = StringField(required=False)
    numero_interior = StringField(required=False)
    colonia = StringField(required=False)
    alcaldia_municipio = StringField(required=False)
    cp = StringField(required=False)
    email = StringField(required=False)
    id_identificacion = StringField(required=False)

    events = ListField(ReferenceField(Event))

    def create_account(self) -> CuentaFisica:
        self.estado = Estado.submitted
        self.save()

        optionals = dict(
            apellidoMaterno=self.apellido_materno,
            genero=self.genero,
            entidadFederativa=self.entidad_federativa,
            actividadEconomica=self.actividad_economica,
            calle=self.calle,
            numeroExterior=self.numero_exterior,
            numeroInterior=self.numero_interior,
            colonia=self.colonia,
            alcaldiaMunicipio=self.alcaldia_municipio,
            cp=self.cp,
            email=self.email,
            idIdentificacion=self.id_identificacion,
        )

        # remove if value is None
        optionals = {key: val for key, val in optionals.items() if val}

        try:
            cuenta = stpmex_client.cuentas.alta(
                nombre=self.nombre,
                apellidoPaterno=self.apellido_paterno,
                cuenta=self.cuenta,
                rfcCurp=self.rfc_curp,
                telefono=self.telefono,
                fechaNacimiento=self.fecha_nacimiento,
                paisNacimiento=Pais[self.pais_nacimiento],
                **optionals,
            )
        except Exception as e:
            self.events.append(Event(type=EventType.error, metadata=str(e)))
            self.estado = Estado.error
            self.save()
            raise e
        else:
            self.estado = Estado.succeeded
            self.save()
            return cuenta

    def update_account(self, account: 'PhysicalAccount') -> None:
        attributes_to_update = [
            'rfc_curp',
            'nombre',
            'apellido_paterno',
            'apellido_materno',
            'genero',
            'fecha_nacimiento',
            'actividad_economica',
            'calle',
            'numero_exterior',
            'numero_interior',
            'colonia',
            'alcaldia_municipio',
            'cp',
            'pais_nacimiento',
            'email',
            'id_identificacion',
            'estado',
        ]
        for attr in attributes_to_update:
            setattr(self, attr, getattr(account, attr))
        self.estado = Estado.succeeded
        self.save()


@updated_at.apply
@save_events.apply
@delete_events.apply
class MoralAccount(Account):
    empresa = StringField(required=True)
    pais = StringField(required=False)
    fecha_constitucion = DateTimeField(required=True)
    entidad_federativa = StringField()
    actividad_economica = StringField()

    def create_account(self) -> CuentaMoral:
        self.estado = Estado.submitted
        self.save()
        optionals = dict(
            entidadFederativa=self.entidad_federativa,
            actividadEconomica=self.actividad_economica,
        )
        optionals = {key: val for key, val in optionals.items() if val}

        try:
            cuenta = stpmex_client.cuentas_morales.alta(
                empresa=self.empresa,
                pais=Pais[self.pais],
                fechaConstitucion=self.fecha_constitucion,
                **optionals,
            )
        except Exception as e:
            self.events.append(Event(type=EventType.error, metadata=str(e)))
            self.estado = Estado.error
            self.save()
            raise e
        else:
            self.estado = Estado.succeeded
            self.save()
            return cuenta
