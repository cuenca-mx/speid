import os

RABBIT_URL = os.environ['AMPQ_ADDRESS']
RABBIT_URL_TYPE = os.environ['AMPQ_ADDRESS_TYPE']
QUEUE_BACK = 'cuenca.stp.orden_result'
RPC_QUEUE = 'rpc_queue'
NEW_ORDER_QUEUE = 'cuenca.stp.new_order'
