from datetime import datetime

import click
import pandas

from speid import app
from speid.helpers import callback_helper
from speid.models import Event, Request, Transaction
from speid.types import Estado, EventType


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
    transaction.events.append(
        Event(type=event_type, metadata=str('Reversed by SPEID command'))
    )
    transaction.save()
    return transaction


@speid_group.command()
@click.option(
    '--speid_id', default=None, help='Specific speid id to create_account_',
)
def re_execute_transactions(speid_id):
    """Retry send a transaction to STP, it takes the values
    of the event created before
    """
    transaction = Transaction.objects.get(speid_id=speid_id)

    if transaction is None:
        raise ValueError('Transaction not found')

    transaction.create_order()


@speid_group.command()
@click.option(
    '--transactions',
    default='transactions.csv',
    help='CSV file with transactions',
)
@click.option('--events', default='events.csv', help='CSV file with events')
@click.option(
    '--requests', default='requests.csv', help='CSV file with requests'
)
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
    transactions_list = pandas.read_csv(
        transactions,
        converters=dict(
            institucion_ordenante=lambda x: str(x),
            institucion_beneficiaria=lambda x: str(x),
            cuenta_ordenante=lambda x: str(x),
            cuenta_beneficiario=lambda x: str(x),
        ),
    )
    transactions_list = transactions_list.where(
        (pandas.notnull(transactions_list)), None
    )
    events_list = pandas.read_csv(events)
    events_list = events_list.where((pandas.notnull(events_list)), None)
    transactions = []
    for _, t in transactions_list.iterrows():
        t['stp_id'] = t['orden_id']
        del t['orden_id']
        if t['estado'] in ['ND', 'success', 'liquidacion']:
            t['estado'] = 'succeeded'
        t['institucion_beneficiaria'] = str(t['institucion_beneficiaria'])
        t['cuenta_ordenante'] = str(t['cuenta_ordenante'])
        t['cuenta_beneficiario'] = str(t['cuenta_beneficiario'])

        transaction = Transaction(**t)

        transaction_events = events_list[events_list.transaction_id == t['id']]
        for _, e in transaction_events.iterrows():
            transaction.events.append(
                Event(
                    created_at=datetime.fromisoformat(e['created_at']),
                    type=EventType[e['type']],
                    metadata=e['meta'],
                )
            )

        transaction.id = None
        transactions.append(transaction)

    requests_list = pandas.read_csv(requests)
    requests_list = requests_list.where((pandas.notnull(requests_list)), None)
    requests = []
    for _, r in requests_list.iterrows():
        r['method'] = r['method'].upper()
        request = Request(**r)
        request.id = None
        requests.append(request)

    Request.objects.insert(requests)
    for transaction in transactions:
        transaction.save()


if __name__ == "__main__":
    re_execute_transactions()
