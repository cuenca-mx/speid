import os

AMPQ_ADDRESS = os.environ['AMPQ_ADDRESS']

broker_url = AMPQ_ADDRESS
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
