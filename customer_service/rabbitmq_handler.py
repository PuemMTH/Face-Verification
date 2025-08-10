import pika
import json
import os
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

# Initialize Rich Console
console = Console()

class QueueHandler:
    def __init__(self, model_handler):
        self.model_handler = model_handler
        self.connection = None
        self.channel = None
        self.queue = None

    def connect(self):
        """Establish connection to RabbitMQ"""
        rabbitmq_url = os.getenv('RABBITMQ_URL')
        self.queue = os.getenv('RABBITMQ_QUEUE')
        
        if rabbitmq_url is None:
            raise ValueError("RABBITMQ_URL environment variable is not set")
        
        console.print(f"[bold blue]Connecting to RabbitMQ using URL:[/bold blue] [cyan]{rabbitmq_url}[/cyan]")
        
        params = pika.URLParameters(rabbitmq_url)
        self.connection = pika.BlockingConnection(params)
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=self.queue)
        self.channel.basic_qos(prefetch_count=1)
        console.print(f"[bold green]Successfully connected to RabbitMQ and listening on queue:[/bold green] [yellow]{self.queue}[/yellow]")

    def on_request(self, ch, method, props, body):
        """Handle incoming RabbitMQ requests"""
        try:
            json_body = json.loads(body)
            console.print(f"[bold cyan]Received request:[/bold cyan] [white]{json_body}[/white]")

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
                console.print(f"[bold green]Processing file:[/bold green] [yellow]{json_body['file']}[/yellow]")
                response = self.model_handler.process_image(
                    file_path=json_body['file']
                )
                console.print(f"[bold blue]Processing result:[/bold blue] [white]{response}[/white]")

        except Exception as e:
            console.print(f"[bold red]Error processing request:[/bold red] [red]{str(e)}[/red]")
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
            queue=self.queue,
            on_message_callback=self.on_request
        )
        console.print("[bold yellow]Waiting for messages. To exit press CTRL+C[/bold yellow]")
        self.channel.start_consuming()

    def close(self):
        """Close the connection"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()
            console.print("[bold green]Connection closed[/bold green]") 