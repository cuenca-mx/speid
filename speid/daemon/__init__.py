import logging
import os

import logstash

elastic_host = os.environ['ELASTIC_HOST']
elastic_port = os.environ['ELASTIC_PORT']
log_level = os.environ['CELERY_LOG_LEVEL']
if log_level == 'debug':
    level = logging.DEBUG
else:
    level = logging.INFO


def initialize_logstash(logger=None, loglevel=level, **kwargs):
    handler = logstash.TCPLogstashHandler(
        elastic_host, elastic_port, tags=['celery'],
        message_type='celery', version=1
    )
    handler.setLevel(loglevel)
    logger.addHandler(handler)
    return logger


from celery.signals import after_setup_task_logger
after_setup_task_logger.connect(initialize_logstash)

from celery.signals import after_setup_logger
after_setup_logger.connect(initialize_logstash)
