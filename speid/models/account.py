from mongoengine import (
    DateTimeField,
    Document,
    IntField,
    ListField,
    ReferenceField,
    StringField,
)
from stpmex.resources import CuentaFisica
from stpmex.types import Genero

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
    created_at = date_now()
    updated_at = DateTimeField()
    estado = EnumField(Estado, default=Estado.created)

    nombre = StringField()
    apellido_paterno = StringField()
    apellido_materno = StringField(required=False)
    cuenta = StringField(unique=True)
    rfc_curp = StringField()
    telefono = StringField()

    genero = EnumField(Genero, required=False)
    fecha_nacimiento = DateTimeField(required=False)
    entidad_federativa = IntField(required=False)
    actividad_economica = IntField(required=False)
    calle = StringField(required=False)
    numero_exterior = StringField(required=False)
    numero_interior = StringField(required=False)
    colonia = StringField(required=False)
    alcaldia_municipio = StringField(required=False)
    cp = StringField(required=False)
    pais = IntField(required=False)
    email = StringField(required=False)
    id_identificacion = StringField(required=False)

    events = ListField(ReferenceField(Event))

    def create_account(self) -> CuentaFisica:
        self.estado = Estado.submitted
        self.save()

        optionals = dict(
            apellidoMaterno=self.apellido_materno,
            genero=self.genero,
            fechaNacimiento=self.fecha_nacimiento,
            entidadFederativa=self.entidad_federativa,
            actividadEconomica=self.actividad_economica,
            calle=self.calle,
            numeroExterior=self.numero_exterior,
            numeroInterior=self.numero_interior,
            colonia=self.colonia,
            alcaldiaMunicipio=self.alcaldia_municipio,
            cp=self.cp,
            pais=self.pais,
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

    def update_account(self, account: 'Account') -> None:
        optionals = dict(
            apellidoMaterno=account.apellido_materno,
            genero=account.genero,
            fechaNacimiento=account.fecha_nacimiento,
            entidadFederativa=account.entidad_federativa,
            actividadEconomica=account.actividad_economica,
            calle=account.calle,
            numeroExterior=account.numero_exterior,
            numeroInterior=account.numero_interior,
            colonia=account.colonia,
            alcaldiaMunicipio=account.alcaldia_municipio,
            cp=account.cp,
            pais=account.pais,
            email=account.email,
            idIdentificacion=account.id_identificacion,
        )

        # remove if value is None
        optionals = {key: val for key, val in optionals.items() if val}

        if self.rfc_curp != account.rfc_curp:
            try:
                stpmex_client.cuentas.update(
                    old_rfc_curp=self.rfc_curp,
                    nombre=account.nombre,
                    apellidoPaterno=account.apellido_paterno,
                    cuenta=account.cuenta,
                    rfcCurp=account.rfc_curp,
                    telefono=account.telefono,
                    **optionals,
                )
            except Exception as exc:
                self.events.append(
                    Event(type=EventType.error, metadata=str(exc))
                )
                self.estado = Estado.error
                self.save()
                raise exc
        self.rfc_curp = account.rfc_curp
        self.nombre = account.nombre
        self.apellido_paterno = account.apellido_paterno
        self.apellido_materno = account.apellido_materno
        self.genero = account.genero
        self.fecha_nacimiento = account.fecha_nacimiento
        self.actividad_economica = account.actividad_economica
        self.calle = account.calle
        self.numero_exterior = account.numero_exterior
        self.numero_interior = account.numero_interior
        self.colonia = account.colonia
        self.alcaldia_municipio = account.alcaldia_municipio
        self.cp = account.cp
        self.pais = account.pais
        self.email = account.email
        self.id_identificacion = account.id_identificacion
        self.estado = Estado.succeeded
        self.save()
