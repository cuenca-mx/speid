from mongoengine import DoesNotExist
from sentry_sdk import capture_exception

from speid.helpers.transaction_helper import process_incoming_transaction
from speid.models import Transaction
from speid.tasks import celery
from speid.types import Estado


@celery.task(bind=True, max_retries=5)
def create_transactions(self, transactions: list):
    try:
        execute(transactions)
    except Exception as e:
        capture_exception(e)
        self.retry(countdown=600, exc=e)


def execute(transactions: list):
    for transaction in transactions:
        try:
            previous_transaction = Transaction.objects.get(
                clave_rastreo=transaction['ClaveRastreo'],
                fecha_operacion=transaction['FechaOperacion'],
            )
            if previous_transaction.estado == Estado.error:
                # Not in cuenca
                previous_transaction.confirm_callback_transaction()
                previous_transaction.save()
        except DoesNotExist:
            # Not in speid
            process_incoming_transaction(transaction)
