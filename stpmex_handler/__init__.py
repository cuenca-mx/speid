import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import stpmex
import boto3

database_uri = os.getenv('DATABASE_URI')
stp_private_location = os.getenv('STP_PRIVATE_LOCATION')
stp_bucket_s3 = os.getenv('STP_BUCKET_S3')
stp_key_s3 = os.getenv('STP_PRIVATE_KEY')
wsdl_path = os.getenv('STP_WSDL')
stp_empresa = os.getenv('STP_EMPRESA')
priv_key_passphrase = os.getenv('STP_KEY_PASSPHRASE')
stp_prefijo = os.getenv('STP_PREFIJO')
stpmex_handler_env = os.getenv('STPMEX_HANDLER_ENV', '')

app = Flask('stpmex-handler')

app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Al final debería de eliminarse las siguientes líneas para guardar en RabbitMQ
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Obtiene la private key de S3
s3 = boto3.resource('s3')
s3.Bucket(stp_bucket_s3).download_file(stp_key_s3, stp_private_location)

# Configura el cliente STP
with open(stp_private_location) as fp:
    private_key = fp.read()
stpmex.configure(wsdl_path=wsdl_path,
                 empresa=stp_empresa,
                 priv_key=private_key,
                 priv_key_passphrase=priv_key_passphrase,
                 prefijo=int(stp_prefijo))

if not stpmex_handler_env.lower() == 'prod':
    import stpmex_handler.commands
