from mongoengine import DoesNotExist
from sentry_sdk import capture_exception

from speid.models import Account, Event
from speid.tasks import celery
from speid.types import EventType
from speid.validations import Account as AccountValidation


@celery.task(bind=True, max_retries=None)
def create_account(self, account_dict: dict):
    try:
        account_val = AccountValidation(**account_dict)
    except (TypeError, ValueError) as e:
        capture_exception(e)
        return  # Should not be retried if the're validation errors

    # Look for previous accounts
    account = account_val.transform()
    try:
        previous_account = Account.objects.get(cuenta=account.cuenta)
    except DoesNotExist:
        account.save()
    else:
        account = previous_account
        account.events.append(Event(type=EventType.retry))

    account.create_account()
