from mongoengine import DateTimeField, IntField, StringField
from stpmex.exc import StpmexException
from stpmex.resources import Cuenta
from stpmex.types import Genero

from speid.models import DocumentBaseMixin, Event
from speid.models.helpers import EnumField, date_now, updated_at
from speid.processors import stpmex_client
from speid.types import Estado, EventType


@updated_at.apply
class Account(DocumentBaseMixin):
    created_at = date_now()
    updated_at = DateTimeField()
    stp_id = IntField()
    estado = EnumField(Estado, default=Estado.created)

    nombre: StringField()
    apellido_paterno: StringField()
    apellido_materno: StringField(default=None)
    cuenta: StringField()
    rfc_curp: StringField()
    telefono: StringField()
    genero: EnumField(Genero)

    fecha_nacimiento: DateTimeField(default=None)
    entidad_federativa: IntField(default=None)
    actividad_economica: IntField(default=None)
    calle: StringField(default=None)
    numero_exterior: StringField(default=None)
    numero_interior: StringField(default=None)
    colonia: StringField(default=None)
    alcaldia_municipio: StringField(default=None)
    cp: StringField(default=None)
    pais: IntField(default=None)
    email: StringField(default=None)
    id_identificacion: StringField(default=None)

    def create_account(self) -> Cuenta:
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
        except StpmexException as e:
            self.events.append(Event(type=EventType.error, metadata=str(e)))
            self.estado = Estado.error
            self.save()
            raise e
        else:
            self.stp_id = cuenta.id
            self.estado = Estado.succeeded
            self.save()
            return cuenta
