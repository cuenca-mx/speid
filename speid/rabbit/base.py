import pika
import uuid
from speid.rabbit import CONNECTION

RPC_QUEUE = 'rpc_queue'
NEW_ORDER_QUEUE = 'cuenca.stp.new_order'


class RpcClient():
    def __init__(self):
        # Sets a unique channel
        self.channel = CONNECTION.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        # Define a function to be called when an answer is received
        self.channel.basic_consume(self.on_response, no_ack=True,
                                   queue=self.callback_queue)
        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        # Only handle those with same correlation ID requested
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, element):
        self.response = None
        # Assigns a unique ID
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(exchange='',
                                   routing_key=RPC_QUEUE,
                                   properties=pika.BasicProperties(
                                       reply_to=self.callback_queue,
                                       correlation_id=self.corr_id
                                   ),
                                   body=str(element))

        # Wait to the response up to 15 seconds
        while self.response is None:
            CONNECTION.process_data_events(15)

        return self.response


class ConfirmModeClient():
    def __init__(self, queue):
        self.channel = CONNECTION.channel()
        # Make the queue durable in order to not miss any element
        # TODO Use the channel in Confirm mode to make it more persistent
        self.channel.queue_declare(queue=queue, durable=True)
        self.queue = queue

    def call(self, element):
        # Not using an exchange as we only deliver one task to one subscriber
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue,
                                   body=str(element),
                                   properties=pika.BasicProperties(
                                       delivery_mode=2  # Message persistent
                                   ))
