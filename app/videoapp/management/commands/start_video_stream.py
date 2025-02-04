from django.core.management.base import BaseCommand
from videoapp.consumers import VideoStreamPublisher

class Command(BaseCommand):
    help = "Start publishing video frames to RabbitMQ"

    def handle(self, *args, **options):
        publisher = VideoStreamPublisher()
        publisher.publish_frames()
