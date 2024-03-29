__all__ = ['STP_EMPRESA', 'commands', 'models', 'views']

import datetime as dt
import json
import os
from enum import Enum

import boto3
import sentry_sdk
from flask import Flask
from flask_mongoengine import MongoEngine
from python_hosts import Hosts, HostsEntry
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.flask import FlaskIntegration


class CJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            encoded = o.name
        elif isinstance(o, dt.datetime):
            encoded = o.isoformat() + 'Z'
        else:
            try:
                encoded = o.to_dict()
            except AttributeError:  # pragma: no cover
                encoded = super().default(o)
        return encoded


def configure_environment():
    # Descarga la private key de S3
    if 'AWS_ACCESS_KEY_ID' in os.environ:
        s3 = boto3.client('s3')
        s3.download_file(STP_BUCKET_S3, STP_PRIVATE_KEY, STP_PRIVATE_LOCATION)
        s3.download_file(STP_BUCKET_S3, STP_VERIFY_CERT, STP_VERIFY_CERT)

    # Edita archivo hosts si es necesario
    if os.environ['EDIT_HOSTS'] == 'true':
        host_ip = os.environ['HOST_IP']
        host_ad = os.environ['HOST_AD']
        hosts = Hosts()
        new_entry = HostsEntry(
            entry_type='ipv4', address=host_ip, names=[host_ad]
        )
        hosts.add([new_entry])
        hosts.write()


# Configura sentry
sentry_sdk.init(
    dsn=os.environ['SENTRY_DSN'],
    integrations=[FlaskIntegration(), CeleryIntegration()],
)

# Obtiene las variables de ambiente
STP_PRIVATE_LOCATION = os.environ['STP_PRIVATE_LOCATION']
STP_BUCKET_S3 = os.environ['STP_BUCKET_S3']
STP_PRIVATE_KEY = os.environ['STP_PRIVATE_KEY']
STP_VERIFY_CERT = os.environ['STP_VERIFY_CERT']
STP_WSDL = os.environ['STP_WSDL']
STP_EMPRESA = os.environ['STP_EMPRESA']
STP_PREFIJO = os.environ['STP_PREFIJO']
DATABASE_URI = os.environ['DATABASE_URI']

app = Flask('speid')

app.config['MONGODB_HOST'] = DATABASE_URI

app.json_encoder = CJSONEncoder  # type: ignore

db = MongoEngine(app)

configure_environment()

# Configura el cliente STP
with open(STP_PRIVATE_LOCATION) as fp:
    private_key = fp.read()

from . import commands, models, views  # noqa: E402 isort:skip
