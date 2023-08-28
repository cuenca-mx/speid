import datetime as dt

import click
import pytz
from mongoengine import DoesNotExist
from stpmex.business_days import get_next_business_day
from stpmex.types import Estado as StpEstado

from speid import app
from speid.helpers.callback_helper import set_status_transaction
from speid.helpers.transaction_helper import process_incoming_transaction
from speid.models import Event, Transaction
from speid.processors import stpmex_client
from speid.types import Estado, EventType

ESTADOS_DEPOSITOS_VALIDOS = {
    StpEstado.confirmada,
    StpEstado.liquidada,
    StpEstado.traspaso_liquidado,
}

TIPOS_PAGO_DEVOLUCION = {0, 16, 17, 18, 23, 24}


@app.cli.group('speid')
def speid_group():
    """Perform speid actions."""


@speid_group.command('callback-spei-transaction')
@click.argument('transaction_id', type=str)
@click.argument('transaction_status', type=str)
def callback_spei_transaction(transaction_id, transaction_status):
    """Establece el estado de la transacción,
    valores permitidos succeeded y failed"""
    transaction = Transaction.objects.get(id=transaction_id)
    if transaction_status == Estado.succeeded.value:
        transaction.estado = Estado.succeeded
        event_type = EventType.completed
    elif transaction_status == Estado.failed.value:
        transaction.estado = Estado.failed
        event_type = EventType.error
    else:
        raise ValueError('Invalid event type')
    set_status_transaction(transaction.speid_id, transaction.estado.value)
    transaction.events.append(
        Event(type=event_type, metadata=str('Reversed by SPEID command'))
    )
    transaction.save()


@speid_group.command('re-execute-transactions')
@click.argument('speid_id', type=str)
def re_execute_transactions(speid_id):
    """Retry send a transaction to STP, it takes the values
    of the event created before
    """
    try:
        transaction = Transaction.objects.get(speid_id=speid_id)
    except DoesNotExist:
        raise ValueError('Transaction not found')

    transaction.create_order()


@speid_group.command('reconciliate-deposits')
@click.argument('fecha_operacion', type=click.DateTime())
@click.argument('claves_rastreo', type=str)
def reconciliate_deposits(
    fecha_operacion: dt.datetime, claves_rastreo: str
) -> None:

    claves_rastreo_filter = set(claves_rastreo.split(','))
    mex_query_date = dt.datetime.utcnow().astimezone(
        pytz.timezone('America/Mexico_City')
    )

    if fecha_operacion.date() < get_next_business_day(mex_query_date):
        recibidas = stpmex_client.ordenes.consulta_recibidas(fecha_operacion)
    else:
        recibidas = stpmex_client.ordenes.consulta_recibidas()

    no_procesadas = []
    for recibida in recibidas:
        if recibida.claveRastreo not in claves_rastreo_filter:
            continue
        # Se ignora los tipos pago devolución debido a que
        # el estado de estas operaciones se envían
        # al webhook `POST /orden_events`
        if recibida.tipoPago in TIPOS_PAGO_DEVOLUCION:
            no_procesadas.append(recibida.claveRastreo)
            continue

        if recibida.estado not in ESTADOS_DEPOSITOS_VALIDOS:
            no_procesadas.append(recibida.claveRastreo)
            continue

        try:
            Transaction.objects.get(
                clave_rastreo=recibida.claveRastreo,
                fecha_operacion=recibida.fechaOperacion,
            )
        except DoesNotExist:
            # Para reutilizar la lógica actual para abonar depósitos se
            # hace una conversión del modelo de respuesta de
            # la función `consulta_recibidas` al modelo del evento que envía
            # STP por el webhook en `POST /ordenes`
            stp_request = dict(
                Clave=recibida.idEF,
                FechaOperacion=recibida.fechaOperacion.strftime('%Y%m%d'),
                InstitucionOrdenante=recibida.institucionContraparte,
                InstitucionBeneficiaria=recibida.institucionOperante,
                ClaveRastreo=recibida.claveRastreo,
                Monto=recibida.monto,
                NombreOrdenante=recibida.nombreOrdenante,
                TipoCuentaOrdenante=recibida.tipoCuentaOrdenante,
                CuentaOrdenante=recibida.cuentaOrdenante,
                RFCCurpOrdenante=recibida.rfcCurpOrdenante,
                NombreBeneficiario=recibida.nombreBeneficiario,
                TipoCuentaBeneficiario=recibida.tipoCuentaBeneficiario,
                CuentaBeneficiario=recibida.cuentaBeneficiario,
                RFCCurpBeneficiario=getattr(
                    recibida, 'rfcCurpBeneficiario', 'NA'
                ),
                ConceptoPago=recibida.conceptoPago,
                ReferenciaNumerica=recibida.referenciaNumerica,
                Empresa=recibida.empresa,
            )
            click.echo(f'Depósito procesado: {recibida.claveRastreo}')
            process_incoming_transaction(stp_request)
        else:
            no_procesadas.append(recibida.claveRastreo)

    click.echo(f'No procesadas: {no_procesadas}')


if __name__ == "__main__":
    re_execute_transactions()  # pragma: no cover
