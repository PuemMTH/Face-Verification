import pika
import uuid
import json
import os

class RabbitMQClient(object):
    
    def __init__(self, qname, rabbitmq_url, local=False):
        self.qname = qname
        self.rabbitmq_url = rabbitmq_url
        self.local = local
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.response = None
        self.corr_id = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            if self.local:
                print("Connecting to local RabbitMQ at localhost")
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            else:
                print(f"Connecting to RabbitMQ using URL: {self.rabbitmq_url}")
                params = pika.URLParameters(self.rabbitmq_url)
                self.connection = pika.BlockingConnection(params)

            self.channel = self.connection.channel()
            
            # Check if queue exists and declare it if it doesn't
            try:
                self.channel.queue_declare(queue=self.qname, passive=True)
                print(f"Queue '{self.qname}' already exists")
            except pika.exceptions.ChannelClosedByBroker as e:
                if "NOT_FOUND" in str(e):
                    # Queue doesn't exist, create it
                    self.channel.queue_declare(queue=self.qname, durable=False)
                    print(f"Created queue '{self.qname}'")
                else:
                    raise e
            
            # Declare callback queue for responses
            result = self.channel.queue_declare('', exclusive=True)
            self.callback_queue = result.method.queue

            self.channel.basic_consume(
                queue=self.callback_queue,
                on_message_callback=self.on_response,
                auto_ack=True)
            
            print(f"Successfully connected to RabbitMQ and declared queue: {self.qname}")
            return True
        except pika.exceptions.AMQPConnectionError as e:
            print(f"AMQP Connection Error: {str(e)}")
            return False
        except pika.exceptions.ChannelClosedByBroker as e:
            print(f"Channel Closed by Broker: {str(e)}")
            return False
        except Exception as e:
            print(f"Failed to connect to RabbitMQ: {str(e)}")
            return False

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, data, metadata):
        """Send a message to RabbitMQ and wait for response"""
        if not self.connection or self.connection.is_closed:
            if not self.connect():
                raise ConnectionError("Failed to connect to RabbitMQ")
        
        self.response = None
        self.corr_id = str(uuid.uuid4())
        
        # Send the actual data in the body
        self.channel.basic_publish(
            exchange='',
            routing_key=self.qname,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                headers=metadata
            ),
            body=json.dumps(data))
        
        print(f" [x] Submit new request for {self.qname}")
        while self.response is None:
            self.connection.process_data_events()
        return self.response
    
    def close(self):
        """Close the RabbitMQ connection"""
        if hasattr(self, 'connection') and self.connection and not self.connection.is_closed:
            self.connection.close()