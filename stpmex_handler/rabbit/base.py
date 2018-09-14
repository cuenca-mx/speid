import pika
import uuid
import os

RABBIT_URL = os.getenv('RABBIT_URL')
RPC_QUEUE = 'rpc_queue'


class Base:
    def __init__(self):
        # TODO Validate this instruction doesn't create a new connection on each call, otherwise move it to __init__.py
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_URL))
        self.channel = self.connection.channel()


class RpcClient(Base):
    def __init__(self):
        super().__init__()
        # Sets a unique channel
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        # Define a function to be called when an answer is received
        self.channel.basic_consume(self.on_response, no_ack=True, queue=self.callback_queue)
        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        # Only handle those with the correlation ID same as requested
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

        # Wait to the response
        # TODO How much time to wait for this response?
        while self.response is None:
            self.connection.process_data_events()

        return self.response


class ConfirmModeClient(Base):
    def __init__(self, queue):
        super().__init__()
        # Make the queue durable in order to not miss any element
        # TODO Use the channel in Confirm mode to make it more persistent
        self.queue = queue
        self.channel.queue_declare(queue=queue, durable=True)

    def call(self, element):
        # Not using an exchange as we only deliver one task to one subscriber
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue,
                                   body=str(element),
                                   properties=pika.BasicProperties(
                                       delivery_mode=2    # Makes the message persistent
                                   ))
