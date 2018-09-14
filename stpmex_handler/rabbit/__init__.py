from .base import RpcClient, ConfirmModeClient
import os

RABBIT_URL = os.getenv('RABBIT_URL')
RPC_QUEUE = 'rpc_queue'
