import pika
import json
from dotenv import load_dotenv
load_dotenv()
import os

class QueueHandler:
    def __init__(self, model_handler):
        self.model_handler = model_handler
        self.connection = None
        self.channel = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        host = os.getenv('RABBITMQ_HOST', 'localhost')
        port = int(os.getenv('RABBITMQ_PORT', '5672'))
        username = os.getenv('RABBITMQ_USER', 'ipu_user')
        password = os.getenv('RABBITMQ_PASS', 'ipu_password')
        queue = os.getenv('RABBITMQ_QUEUE', 'face_verification_queue')
        
        print(f"Connecting to RabbitMQ at {host}:{port} with user: {username}")
        
        credentials = pika.PlainCredentials(username, password)
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=host,
                port=port,
                credentials=credentials
            )
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=queue)
        self.channel.basic_qos(prefetch_count=1)
        print(f"Successfully connected to RabbitMQ and listening on queue: {queue}")

    def on_request(self, ch, method, props, body):
        """Handle incoming RabbitMQ requests"""
        try:
            json_body = json.loads(body)
            print(f"Received request: {json_body}")

            if 'file' not in json_body and 'files' not in json_body:
                response = json.dumps({
                    'OK': False,
                    'error': 'Missing required "file" or "files" field in request'
                })
            elif 'files' in json_body:
                response = json.dumps({
                    'OK': False,
                    'error': 'Batch processing not supported'
                })
            else:
                print(f"Processing file: {json_body['file']}")
                response = self.model_handler.process_image(
                    file_path=json_body['file']
                )
                print(f"Processing result: {response}")

        except Exception as e:
            print(f"Error processing request: {str(e)}")
            response = json.dumps({
                'OK': False,
                'error': str(e)
            })

        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=response
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def start_consuming(self):
        """Start consuming messages"""
        self.channel.basic_consume(
            queue=os.getenv('RABBITMQ_QUEUE'),
            on_message_callback=self.on_request
        )
        print("Waiting for messages. To exit press CTRL+C")
        self.channel.start_consuming()

    def close(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            print("Connection closed") 