import os

import boto3
import stpmex
from celery import Celery

# Obtiene las variables de ambiente
stp_private_location = os.getenv('STP_PRIVATE_LOCATION')
stp_bucket_s3 = os.getenv('STP_BUCKET_S3')
stp_key_s3 = os.getenv('STP_PRIVATE_KEY')
wsdl_path = os.getenv('STP_WSDL')
stp_empresa = os.getenv('STP_EMPRESA')
priv_key_passphrase = os.getenv('STP_KEY_PASSPHRASE')
stp_prefijo = os.getenv('STP_PREFIJO')

# Inicia Celery y lo configura usando el archivo celeryconfig.py
app = Celery('stp_client')
app.config_from_object('speid.daemon.celeryconfig')

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

if __name__ == '__main__':
    app.start()
