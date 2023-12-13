import datetime as dt

import click
from mongoengine import DoesNotExist

from speid import app
from speid.helpers.callback_helper import set_status_transaction
from speid.models import Event, Transaction
from speid.tasks.transactions import apply_stp_deposit
from speid.types import Estado, EventType


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
    claves_rastreo_set = set(claves_rastreo.split(','))
    not_processed = []

    for clave_rastreo in claves_rastreo_set:
        try:
            Transaction.objects.get(
                clave_rastreo=clave_rastreo,
                fecha_operacion=fecha_operacion.date(),
            )
        except DoesNotExist:
            processed_clave_rastreo = apply_stp_deposit(
                clave_rastreo, fecha_operacion.date()
            )
            if not processed_clave_rastreo:
                not_processed.append(clave_rastreo)
        else:
            not_processed.append(clave_rastreo)

    click.echo(f'No procesadas: {not_processed}')


if __name__ == "__main__":
    re_execute_transactions()  # pragma: no cover
