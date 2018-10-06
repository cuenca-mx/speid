import os

import boto3
from botocore import UNSIGNED
from botocore.config import Config
import stpmex
from celery import Celery
from python_hosts import Hosts, HostsEntry

# Obtiene las variables de ambiente
stp_private_location = os.environ['STP_PRIVATE_LOCATION']
stp_bucket_s3 = os.environ['STP_BUCKET_S3']
stp_key_s3 = os.environ['STP_PRIVATE_KEY']
wsdl_path = os.environ['STP_WSDL']
stp_empresa = os.environ['STP_EMPRESA']
priv_key_passphrase = os.environ['STP_KEY_PASSPHRASE']
stp_prefijo = os.environ['STP_PREFIJO']
edit_hosts = os.environ['EDIT_HOSTS']

# Inicia Celery y lo configura usando el archivo celeryconfig.py
app = Celery('stp_client')
app.config_from_object('speid.daemon.celeryconfig')

# Obtiene la private key de S3
if "AWS_ACCESS_KEY_ID" in os.environ:
    s3 = boto3.client('s3')
else:
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
s3.download_file(stp_bucket_s3, stp_key_s3, stp_private_location)

# Edita archivo hosts si es necesario
if edit_hosts == 'true':
    host_ip = os.environ['HOST_IP']
    host_ad = os.environ['HOST_AD']
    hosts = Hosts()
    new_entry = HostsEntry(
        entry_type='ipv4',
        address=host_ip,
        names=[host_ad]
    )
    hosts.add([new_entry])
    hosts.write()

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
