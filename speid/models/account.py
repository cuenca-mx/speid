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
        remove = []
        for k, v in optionals.items():
            if v is None:
                remove.append(k)
        for k in remove:
            optionals.pop(k)

        try:
            cuenta = stpmex_client.cuentas.alta(
                nombre=self.nombre,
                apellidoPaterno=self.apellido_paterno,
                cuenta=self.cuenta,
                rfcCurp=self.rfc_curp,
                telefono=self.telefono,
                **optionals,
            )
        except (Exception) as e:
            self.events.append(Event(type=EventType.error, metadata=str(e)))
            self.estado = Estado.error
            self.save()
            raise e
        else:
            self.estado = Estado.succeeded
            self.save()
            return cuenta
