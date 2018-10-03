import os
import pika

RABBIT_URL = os.getenv('AMPQ_ADDRESS')
RABBIT_URL_TYPE = os.getenv('AMPQ_ADDRESS_TYPE')

if RABBIT_URL_TYPE == 'url':
    parameters = pika.URLParameters(RABBIT_URL)
else:
    parameters = pika.ConnectionParameters(host=RABBIT_URL)
CONNECTION = pika.BlockingConnection(parameters)
