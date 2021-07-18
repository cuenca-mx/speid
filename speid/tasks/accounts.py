from mongoengine import DoesNotExist
from pydantic import ValidationError
from sentry_sdk import capture_exception
from stpmex.exc import InvalidRfcOrCurp, StpmexException
from stpmex.resources.cuentas import Cuenta

from speid.models import Account, Event
from speid.tasks import celery
from speid.types import Estado, EventType
from speid.validations import Account as AccountValidation

COUNTDOWN = 600


@celery.task(bind=True, max_retries=10)
def create_account(self, account_dict: dict) -> None:
    try:
        execute_create_account(account_dict)
    except (InvalidRfcOrCurp, ValidationError) as exc:
        capture_exception(exc)
    except Exception as exc:
        capture_exception(exc)
        self.retry(countdown=COUNTDOWN, exc=exc)  # Reintenta en 10 minutos


def execute_create_account(account_dict: dict):
    account_val = AccountValidation(**account_dict)  # type: ignore
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
        validation_model = AccountValidation(**account_dict)  # type: ignore
        account = Account.objects.get(cuenta=validation_model.cuenta)
        account.update_account(validation_model.transform())
    except ValidationError as exc:
        capture_exception(exc)
    except DoesNotExist:
        create_account.apply((account_dict,))
    except Exception as exc:
        capture_exception(exc)
        self.retry(countdown=COUNTDOWN, exc=exc)


@celery.task(bind=True, max_retries=5)
def deactivate_account(self, cuenta: str) -> None:
    # import pdb
    # pdb.set_trace()
    try:
        account = Account.objects.get(cuenta=cuenta)
    except DoesNotExist:
        return

    stp_cuenta = Cuenta(  # type: ignore
        rfcCurp=account.rfc_curp,
        cuenta=account.cuenta,
    )
    try:
        stp_cuenta.baja(stp_cuenta._base_endpoint + '/fisica')
    except StpmexException as exc:
        self.retry(countdown=COUNTDOWN, exc=exc)
    else:
        account.estado = Estado.deactivated
        account.save()
