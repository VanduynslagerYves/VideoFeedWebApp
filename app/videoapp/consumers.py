import cv2
import base64
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth.models import User

class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if self.scope["user"].is_authenticated:
            await self.accept()
            self.camera = cv2.VideoCapture(0) # 0 is default camera
            asyncio.create_task(self.send_video_frames())
        else:
           await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, 'camera'):
            self.camera.release()
    
    async def send_video_frames(self):
        while True:
            success, frame = self.camera.read()
            if not success:
                break

            _, buffer = cv2.imencode('.jpg', frame)
            img_str = base64.b64encode(buffer).decode('utf-8')

            await self.send(text_data=img_str)
            await asyncio.sleep(0.01) # Optional: for smooth streaming