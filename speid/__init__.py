import os

import boto3
import sentry_sdk
import stpmex
from flask import Flask
from flask_mongoengine import MongoEngine
from python_hosts import Hosts, HostsEntry
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.flask import FlaskIntegration

# Configura sentry

sentry_sdk.init(
    dsn=os.environ['SENTRY_DSN'],
    integrations=[FlaskIntegration(), CeleryIntegration()],
)

# Obtiene las variables de ambiente

STP_PRIVATE_LOCATION = os.environ['STP_PRIVATE_LOCATION']
STP_BUCKET_S3 = os.environ['STP_BUCKET_S3']
STP_PRIVATE_KEY = os.environ['STP_PRIVATE_KEY']
STP_WSDL = os.environ['STP_WSDL']
STP_EMPRESA = os.environ['STP_EMPRESA']
STP_KEY_PASSPHRASE = os.environ['STP_KEY_PASSPHRASE']
STP_PREFIJO = os.environ['STP_PREFIJO']
EDIT_HOSTS = os.environ['EDIT_HOSTS']
DATABASE_URI = os.environ['DATABASE_URI']
SPEID_ENV = os.getenv('SPEID_ENV', '')

app = Flask('speid')

app.config['MONGODB_HOST'] = DATABASE_URI

db = MongoEngine(app)

# Descarga la private key de S3
if "AWS_ACCESS_KEY_ID" in os.environ:
    s3 = boto3.client('s3')
    s3.download_file(STP_BUCKET_S3, STP_PRIVATE_KEY, STP_PRIVATE_LOCATION)

# Edita archivo hosts si es necesario
if EDIT_HOSTS == 'true':
    host_ip = os.environ['HOST_IP']
    host_ad = os.environ['HOST_AD']
    hosts = Hosts()
    new_entry = HostsEntry(entry_type='ipv4', address=host_ip, names=[host_ad])
    hosts.add([new_entry])
    hosts.write()

# Configura el cliente STP
with open(STP_PRIVATE_LOCATION) as fp:
    private_key = fp.read()

stpmex.configure(
    wsdl_path=STP_WSDL,
    empresa=STP_EMPRESA,
    priv_key=private_key,
    priv_key_passphrase=STP_KEY_PASSPHRASE,
    prefijo=int(STP_PREFIJO),
)

import speid.models
import speid.views

if not SPEID_ENV.lower() == 'prod':
    import speid.commands
