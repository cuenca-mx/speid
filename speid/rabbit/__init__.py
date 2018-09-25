import os
import pika

RABBIT_URL = os.getenv('AMPQ_ADDRESS')
CONNECTION = pika.BlockingConnection(pika.ConnectionParameters(
    host=RABBIT_URL))
