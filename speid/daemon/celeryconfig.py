import os

from speid.rabbit.base import NEW_ORDER_QUEUE

broker_url = os.getenv('AMPQ_ADDRESS')
task_serializer = 'json'
accept_content = ['json']
task_routes = ('daemon.tasks.route_task', {NEW_ORDER_QUEUE})
