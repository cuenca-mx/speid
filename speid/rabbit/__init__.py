import os
import pika

RABBIT_URL = os.environ['AMPQ_ADDRESS']
RABBIT_URL_TYPE = os.environ['AMPQ_ADDRESS_TYPE']
