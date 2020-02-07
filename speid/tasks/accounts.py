from mongoengine import DoesNotExist
from sentry_sdk import capture_exception

from speid.models import Account, Event
from speid.tasks import celery
from speid.types import Estado, EventType
from speid.validations import Account as AccountValidation


@celery.task(bind=True, max_retries=None)
def create_account(self, account_dict: dict):
    try:
        execute(account_dict)
    except (Exception) as e:
        capture_exception(e)
        self.retry(countdown=600, exc=e)  # Reintenta en 10 minutos


def execute(account_dict: dict):
    account_val = AccountValidation(**account_dict)

    # Look for previous accounts
    account = account_val.transform()
    try:
        previous_account = Account.objects.get(cuenta=account.cuenta)
    except DoesNotExist:
        account.events.append(Event(type=EventType.created))
        account.save()
    else:
        account = previous_account
        account.events.append(Event(type=EventType.retry))

    if account.estado is Estado.succeeded:
        return

    account.create_account()
