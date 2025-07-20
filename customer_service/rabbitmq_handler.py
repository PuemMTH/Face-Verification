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
        credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASSWORD'))
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv('RABBITMQ_HOST'),
                port=os.getenv('RABBITMQ_PORT'),
                credentials=credentials
            )
        )
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=os.getenv('RABBITMQ_QUEUE'))
        self.channel.basic_qos(prefetch_count=1)

    def on_request(self, ch, method, props, body):
        """Handle incoming RabbitMQ requests"""
        try:
            json_body = json.loads(body)

            if 'file' not in json_body and 'files' not in json_body:
                return json.dumps({
                    'OK': False,
                    'error': 'Missing required "file" or "files" field in request'
                })

            if 'files' in json_body:
                return json.dumps({
                    'OK': False,
                    'error': 'Batch processing not supported'
                })
            else:
                response = self.model_handler.process_image(
                    file_path=json_body['file'],
                    folder_path=json_body['folder_path']
                )

        except Exception as e:
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