import os

from stpmex import Client

STP_PRIVATE_LOCATION = os.environ['STP_PRIVATE_LOCATION']
STP_EMPRESA = os.environ['STP_EMPRESA']
STP_KEY_PASSPHRASE = os.environ['STP_KEY_PASSPHRASE']
STP_BASE_URL = os.getenv('STP_BASE_URL', None)
SPEID_ENV = os.getenv('SPEID_ENV', '')


# Configura el cliente STP
with open(STP_PRIVATE_LOCATION) as fp:
    private_key = fp.read()


stpmex_client = Client(
    empresa=STP_EMPRESA,
    priv_key=private_key,
    priv_key_passphrase=STP_KEY_PASSPHRASE,
    demo=SPEID_ENV != 'prod',
    base_url=SPEID_ENV,
)
