import cv2
import base64
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class VideoStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Check if user is authenticated
        if self.scope["user"].is_authenticated:
            # Accept the WebSocket connection
            await self.accept()
            
            # Add the WebSocket to a group named 'video_stream'
            self.group_name = "video_stream"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            # Start streaming if this is the first client
            if not self.get_camera_status():
                await self.start_camera_stream()

        else:
            await self.close()

    async def disconnect(self, close_code):
        # Remove WebSocket from the group when disconnected
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        # Handle any messages received from clients (e.g., pausing, custom requests)
        pass

    async def start_camera_stream(self):
        """Start the camera stream (only if it's not already streaming)."""
        self.set_camera_status(True)
        self.camera = cv2.VideoCapture(0)  # 0 is the default camera
        asyncio.create_task(self.capture_and_broadcast_frames())

    async def capture_and_broadcast_frames(self):
        """Capture frames from the camera and broadcast them to all clients."""
        while True:
            success, frame = self.camera.read()
            if not success:
                break

            # Encode the frame as a JPEG image and then convert to base64
            _, buffer = cv2.imencode('.jpg', frame)
            img_str = base64.b64encode(buffer).decode('utf-8')

            # Send the image string to all clients in the 'video_stream' group
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'send_frame',
                    'image': img_str
                }
            )
            await asyncio.sleep(0.01)  # Adjust frame rate if necessary

    async def send_frame(self, event):
        """Receive frame from the group and send it to the WebSocket client."""
        # Send the frame (image data) to the WebSocket client
        await self.send(text_data=event['image'])

    def get_camera_status(self):
        """Get the current camera streaming status (if it is active)."""
        return getattr(self, 'camera_active', False)

    def set_camera_status(self, status):
        """Set the camera streaming status."""
        self.camera_active = status
