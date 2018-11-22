import os

from speid.queue import NEW_ORDER_QUEUE

broker_url = os.environ['AMPQ_ADDRESS']
task_serializer = 'json'
accept_content = ['json']
task_default_queue = NEW_ORDER_QUEUE
include = ['speid.daemon.tasks']
backend = 'amqp'

