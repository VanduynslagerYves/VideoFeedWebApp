import cv2
import base64
import pika
import time
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from threading import Thread

# RabbitMQ Connection Credentials
RABBITMQ_HOST = "localhost"
RABBITMQ_USER = "admin"
RABBITMQ_PASSWORD = "root0603"
QUEUE_NAME = "video_frames"
PREFETCH_COUNT = 10  # Limit to 1 frame at a time to reduce lag

def get_rabbitmq_connection():
    """ Establishes an authenticated RabbitMQ connection with prefetch settings """
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        credentials=credentials
    ))    
    return connection

class VideoStreamPublisher:
    """ Publishes video frames to RabbitMQ """
    def __init__(self):
        self.connection = get_rabbitmq_connection()
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=QUEUE_NAME)
        self.channel.basic_qos(prefetch_count=PREFETCH_COUNT)  # Limit prefetch to prevent lag
        #self.channel.queue_declare(queue=QUEUE_NAME)
        self.camera = cv2.VideoCapture(0)  # Open default camera

    def publish_frames(self):
        """ Capture frames and send to RabbitMQ """
        while True:
            success, frame = self.camera.read()
            if not success:
                print("[ERROR] Failed to capture frame")
                break

            _, buffer = cv2.imencode('.jpg', frame)
            img_str = base64.b64encode(buffer).decode("utf-8")

            #self.channel.basic_qos()

            self.channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=img_str)

            time.sleep(0.03)

        self.camera.release()
        self.connection.close()

class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        # Authenticate with RabbitMQ
        self.connection = get_rabbitmq_connection()
        self.channel = self.connection.channel()

        # Start a thread to consume frames
        self.thread = Thread(target=self.consume_frames)
        self.thread.start()
        #if self.scope["user"].is_authenticated:
            # await self.accept()
            # self.camera = cv2.VideoCapture(0) # 0 is default camera, TODO: refactor this line, only one client has access to the camera at any time (rabbitmq?)
            # asyncio.create_task(self.send_video_frames())
        #else:
        #   await self.close()

    def consume_frames(self):
        """ Receive frames from RabbitMQ and send to WebSocket """
        for method_frame, properties, body in self.channel.consume(queue=QUEUE_NAME, auto_ack=True):
            asyncio.run(self.send(text_data=body.decode("utf-8")))

    async def disconnect(self, close_code):
        self.connection.close()