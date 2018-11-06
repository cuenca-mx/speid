import os

from speid.queue import NEW_ORDER_QUEUE
import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration

broker_url = os.environ['AMPQ_ADDRESS']
task_serializer = 'json'
accept_content = ['json']
task_default_queue = NEW_ORDER_QUEUE
include = ['speid.daemon.tasks']
backend = 'amqp'

sentry_url = os.environ['SENTRY_DSN']
sentry_sdk.init(dsn=sentry_url,
                integrations=[CeleryIntegration()])
