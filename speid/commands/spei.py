import click
import os

from ast import literal_eval

from speid import app, db
from speid.models import Event
from speid.models import Transaction
from speid.tables.types import State
import stpmex
from stpmex.ordenes import Orden


@click.command()
def re_execute_transactions():
    """Insert new random CLABEs into the db"""

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

    transactions = db.session.query(Transaction)\
        .filter_by(estado='submitted')
    for transaction in transactions:
        try:
            event = db.session.query(Event).\
                filter_by(
                transaction_id=transaction.id,
                type=State.created
            ).order_by(Event.created_at.desc()).first()

            event_retry = Event(
                transaction_id=transaction.id,
                type=State.retry,
                meta=event.meta
            )
            db.session.add(event_retry)
            db.session.commit()
            order_val = literal_eval(event.meta)
            order = Orden(**order_val)

            # Send order to STP
            order.monto = order.monto / 100
            res = order.registra()
            print(res)
        except Exception as exc:
            print(exc)


if __name__ == '__main__':
    re_execute_transactions()
