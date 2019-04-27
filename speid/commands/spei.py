import click
import os

from ast import literal_eval
import stpmex

from speid import app, db
from speid.models import Event
from speid.models import Transaction
from speid.helpers import callback_helper
from speid.tables.types import Estado, State
from speid.daemon.tasks import execute_task


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
    transaction = (db.session.query(Transaction)
                   .filter_by(id=transaction_id).one())
    if transaction_status == Estado.succeeded.name:
        transaction.estado = Estado.succeeded
        state = State.completed
    if transaction_status == Estado.failed.name:
        transaction.estado = Estado.failed
        state = State.error
    callback_helper.set_status_transaction(
        transaction.speid_id,
        dict(estado=transaction.estado.value)
    )
    event = Event(
        transaction_id=transaction.id,
        type=state,
        meta=str('Reverse by command SPEID')
    )
    db.session.add(transaction)
    db.session.add(event)
    db.session.commit()


@speid_group.command()
@click.option('--speid_id', default=None, help='Specific speid id to execute')
def re_execute_transactions(speid_id):
    """Retry send a transaction to STP, it takes the values
    of the event created before
    """
    stp_private_location = os.environ['STP_PRIVATE_LOCATION']
    wsdl_path = os.environ['STP_WSDL']
    stp_empresa = os.environ['STP_EMPRESA']
    priv_key_passphrase = os.environ['STP_KEY_PASSPHRASE']
    stp_prefijo = os.environ['STP_PREFIJO']

    with open(stp_private_location) as fp:
        private_key = fp.read()
    stpmex.configure(wsdl_path=wsdl_path,
                     empresa=stp_empresa,
                     priv_key=private_key,
                     priv_key_passphrase=priv_key_passphrase,
                     prefijo=int(stp_prefijo))
    if speid_id is None:
        transactions = (db.session.query(Transaction)
                        .filter_by(estado='submitted',
                                   orden_id=None))
        for transaction in transactions:
            send_queue(transaction)
    else:
        transaction = (db.session.query(Transaction)
                       .filter_by(speid_id=speid_id,
                                  estado='submitted',
                                  orden_id=None)
                       .first())
        send_queue(transaction)


def send_queue(transaction):
    try:
        event = (db.session.query(Event).
                 filter_by(
            transaction_id=transaction.id,
            type=State.created
        ).order_by(Event.created_at.desc()).first())

        event_retry = Event(
            transaction_id=transaction.id,
            type=State.retry,
            meta=event.meta
        )
        db.session.add(event_retry)
        db.session.commit()
        order_val = literal_eval(event.meta)
        execute_task(order_val)
    except Exception as exc:
        print(exc)


if __name__ == "__main__":
    re_execute_transactions()
