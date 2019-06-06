from datetime import datetime

import click

from speid import app
from speid.helpers import callback_helper
from speid.models import Event, Request, Transaction
from speid.types import Estado, EventType

import pandas


@app.cli.group('speid')
def speid_group():
    """Perform speid actions."""
    pass


@speid_group.command()
@click.argument('transaction_id', type=str)
@click.argument('transaction_status', type=str)
def callback_spei_transaction(transaction_id, transaction_status):
    """Establece el estado de la transacción,
    valores permitidos succeeded y failed"""
    transaction = Transaction.objects.get(id=transaction_id)
    if transaction_status == Estado.succeeded.name:
        transaction.estado = Estado.succeeded
        event_type = EventType.completed
    elif transaction_status == Estado.failed.name:
        transaction.estado = Estado.failed
        event_type = EventType.error
    else:
        raise ValueError('Invalid event type')
    callback_helper.set_status_transaction(
        transaction.speid_id, transaction.estado.name
    )
    transaction.events.append(Event(type=event_type,
                                    metadata=str('Reversed by SPEID command')))
    transaction.save()
    return transaction


@speid_group.command()
@click.option('--speid_id', default=None, help='Specific speid id to execute')
def re_execute_transactions(speid_id):
    """Retry send a transaction to STP, it takes the values
    of the event created before
    """
    transaction = Transaction.objects.get(speid_id=speid_id)

    if transaction is None:
        raise ValueError('Transaction not found')

    order = transaction.get_order()
    transaction.save()

    order.monto = order.monto / 100

    res = order.registra()

    if res is not None and res.id > 0:
        transaction.events.append(Event(type=EventType.completed,
                                        metadata=str(res)))
    else:
        transaction.events.append(Event(type=EventType.error,
                                        metadata=str(res)))

    transaction.save()


@speid_group.command()
@click.option('--transactions', default='transactions.csv',
              help='CSV file with transactions')
@click.option('--events', default='events.csv', help='CSV file with events')
@click.option('--requests', default='requests.csv',
              help='CSV file with requests')
def migrate_from_csv(transactions, events, requests):
    """
    Hace la migración de una base de datos Postgres a MongoDB, los datos deben
     ser exportados a CSV antes de ser ejecutado, se puede utilizar el archivo
     scripts/migrate_postgres_mongo.sh para ejecutar la tarea completa
    :param transactions: Archivo CSV con los datos de las transacciones
    :param events: Archivo CSV con los eventos relacionados a las transacciones
    :param requests: Archivo CSV con los requests
    :return:
    """
    transactions_list = pandas.read_csv(transactions)
    transactions = [Transaction(**t) for t in transactions_list.iterrows()]

    requests_list = pandas.read_csv(requests)
    requests = [Request(**r) for r in requests_list.iterrows()]

    events_list = pandas.read_csv(events)
    for e in events_list.iterrows():
        trx = next(t for t in transactions if t.id == e['transaction_id'])
        trx.events.append(
            Event(
                type=EventType[e['type']],
                metadata=e['meta'],
                created_at=datetime.strptime(e['created_at'] + '00',
                                             '%Y-%m-%d %H:%M:%S.%f%z')
            ))

    for transaction in transactions:
        transaction.save()

    Request.objects.insert(requests)


if __name__ == "__main__":
    re_execute_transactions()
