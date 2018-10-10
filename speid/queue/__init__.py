import os

from celery import Celery

RABBIT_URL = os.environ['AMPQ_ADDRESS']
RABBIT_URL_TYPE = os.environ['AMPQ_ADDRESS_TYPE']
QUEUE_BACK = 'cuenca.stp.orden_result'
RPC_QUEUE = 'rpc_queue'
NEW_ORDER_QUEUE = 'cuenca.stp.new_order'

app = Celery('speid')
app.conf.broker_url = os.environ['AMPQ_ADDRESS']
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.task_default_queue = 'cuenca.speid.order_event'
