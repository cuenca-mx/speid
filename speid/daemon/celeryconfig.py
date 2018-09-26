import os

from speid.rabbit.base import NEW_ORDER_QUEUE

broker_url = os.getenv('AMPQ_ADDRESS')
# broker_url = 'amqp://guest:guest@999.999.99.9:5672/'
task_serializer = 'json'
accept_content = ['json']
# task_routes = ('daemon.tasks.route_task', {NEW_ORDER_QUEUE})
task_default_queue = NEW_ORDER_QUEUE
include = ['speid.daemon.tasks']
