from mongoengine import DoesNotExist
from pydantic import ValidationError
from sentry_sdk import capture_exception
from stpmex.exc import InvalidRfcOrCurp

from speid.models import Account, Event
from speid.tasks import celery
from speid.types import Estado, EventType
from speid.validations import Account as AccountValidation


@celery.task(bind=True, max_retries=60)
def create_account(self, account_dict: dict) -> None:
    try:
        execute_create_account(account_dict)
    except (InvalidRfcOrCurp, ValidationError) as exc:
        capture_exception(exc)
    except Exception as exc:
        capture_exception(exc)
        self.retry(countdown=600, exc=exc)  # Reintenta en 10 minutos


def execute_create_account(account_dict: dict):
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


@celery.task(bind=True, max_retries=0)
def update_account(self, account_dict: dict) -> None:
    try:
        validation_model = AccountValidation(**account_dict)
        account = Account.objects.get(cuenta=validation_model.cuenta)
        account.update_account(validation_model.transform())
    except ValidationError as exc:
        capture_exception(exc)
    except DoesNotExist:
        create_account.apply((account_dict,))
    except Exception as exc:
        capture_exception(exc)
        self.retry(countdown=600, exc=exc)
