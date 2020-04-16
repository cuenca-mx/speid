import re
from mongoengine import DoesNotExist
from sentry_sdk import capture_exception, capture_message

from speid.models import Account, Event
from speid.tasks import celery
from speid.types import Estado, EventType
from speid.validations import Account as AccountValidation


@celery.task(bind=True, max_retries=60)     # Creo que 60 es suficiente
def create_account(self, account_dict: dict):
    try:
        execute(account_dict)
    except Exception as e:
        capture_exception(e)
        self.retry(countdown=600, exc=e)  # Reintenta en 10 minutos


def execute(account_dict: dict):
    account_val = AccountValidation(**account_dict)
    # Para evitar curps que rechazan
    if not account_val.validate_curp_regex():
        capture_message('Invalid curp')
        return
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


@celery.task(bind=True, max_retries=3)
def update_curp(self, account_dict: dict):
    try:
        execute_update(account_dict)
    except Exception as e:
        capture_exception(e)
        self.retry(countdown=300, exc=e)


def execute_update(account_dict: dict):
    account_val = AccountValidation(**account_dict)
    try:
        account = Account.objects.get(cuenta=account_val.cuenta)
    except DoesNotExist as e:
        capture_exception(e)
        return
    new_curp = account_val.rfc_curp
    try:
        account.update_curp(new_curp)
    except ValueError as e:
        capture_exception(e)
