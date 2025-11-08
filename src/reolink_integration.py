"""
Reolink NVR and Camera Integration
Supports RTSP streaming and API integration with Reolink cameras
"""
import cv2
import logging
import requests
from typing import Dict, List, Optional
import json
from threading import Thread

logger = logging.getLogger(__name__)


class ReolinkCamera:
    """Interface with Reolink camera"""

    def __init__(self, ip: str, username: str, password: str, port: int = 554,
                 stream_type: str = 'main', camera_name: str = None):
        """
        Initialize Reolink camera

        Args:
            ip: Camera IP address
            username: Camera username
            password: Camera password
            port: RTSP port (default 554)
            stream_type: Stream type ('main' or 'sub')
            camera_name: Friendly camera name
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.stream_type = stream_type
        self.camera_name = camera_name or f"Reolink_{ip}"

        # RTSP URL format for Reolink
        # rtsp://username:password@ip:port//h264Preview_01_main (for main stream)
        # rtsp://username:password@ip:port//h264Preview_01_sub (for sub stream)
        stream_path = "main" if stream_type == "main" else "sub"
        self.rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}//h264Preview_01_{stream_path}"

        # HTTP API base URL
        self.api_url = f"http://{ip}/cgi-bin/api.cgi"

        logger.info(f"Reolink camera configured: {self.camera_name}")

    def get_rtsp_url(self) -> str:
        """Get RTSP stream URL"""
        return self.rtsp_url

    def get_camera_info(self) -> Optional[Dict]:
        """
        Get camera information via API

        Returns:
            Camera info dict or None
        """
        try:
            payload = [{
                "cmd": "GetDevInfo",
                "action": 0,
                "param": {}
            }]

            response = requests.post(
                self.api_url,
                auth=(self.username, self.password),
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0].get('value', {}).get('DevInfo', {})

        except Exception as e:
            logger.error(f"Failed to get camera info: {e}")

        return None

    def get_motion_detection_status(self) -> bool:
        """
        Check if motion detection is enabled

        Returns:
            True if motion detection enabled
        """
        try:
            payload = [{
                "cmd": "GetMdState",
                "action": 0,
                "param": {"channel": 0}
            }]

            response = requests.post(
                self.api_url,
                auth=(self.username, self.password),
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return data[0].get('value', {}).get('state', 0) == 1

        except Exception as e:
            logger.error(f"Failed to get motion detection status: {e}")

        return False

    def get_ai_detection_status(self) -> Dict:
        """
        Get AI detection status (person, vehicle, animal)

        Returns:
            Dict with AI detection settings
        """
        try:
            payload = [{
                "cmd": "GetAiState",
                "action": 0,
                "param": {"channel": 0}
            }]

            response = requests.post(
                self.api_url,
                auth=(self.username, self.password),
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    ai_state = data[0].get('value', {}).get('AiState', {})
                    return {
                        'person_detection': ai_state.get('people', {}).get('state', 0) == 1,
                        'vehicle_detection': ai_state.get('vehicle', {}).get('state', 0) == 1,
                        'animal_detection': ai_state.get('pet', {}).get('state', 0) == 1
                    }

        except Exception as e:
            logger.error(f"Failed to get AI detection status: {e}")

        return {'person_detection': False, 'vehicle_detection': False, 'animal_detection': False}

    def test_connection(self) -> bool:
        """
        Test camera connection

        Returns:
            True if connection successful
        """
        try:
            cap = cv2.VideoCapture(self.rtsp_url)
            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                return ret
        except Exception as e:
            logger.error(f"Connection test failed: {e}")

        return False


class ReolinkNVR:
    """Interface with Reolink NVR"""

    def __init__(self, ip: str, username: str, password: str, port: int = 554):
        """
        Initialize Reolink NVR

        Args:
            ip: NVR IP address
            username: NVR username
            password: NVR password
            port: RTSP port
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.port = port
        self.api_url = f"http://{ip}/cgi-bin/api.cgi"
        self.cameras = {}

        logger.info(f"Reolink NVR configured: {ip}")

    def discover_cameras(self) -> List[Dict]:
        """
        Discover cameras connected to NVR

        Returns:
            List of camera info dicts
        """
        try:
            payload = [{
                "cmd": "GetChannelstatus",
                "action": 0,
                "param": {}
            }]

            response = requests.post(
                self.api_url,
                auth=(self.username, self.password),
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    channels = data[0].get('value', {}).get('status', [])

                    cameras = []
                    for i, channel in enumerate(channels):
                        if channel.get('online', 0) == 1:
                            camera_info = {
                                'channel': i,
                                'name': channel.get('name', f'Camera {i+1}'),
                                'online': True
                            }
                            cameras.append(camera_info)

                    logger.info(f"Discovered {len(cameras)} cameras on NVR")
                    return cameras

        except Exception as e:
            logger.error(f"Failed to discover cameras: {e}")

        return []

    def get_camera_stream(self, channel: int, stream_type: str = 'main') -> str:
        """
        Get RTSP URL for NVR camera channel

        Args:
            channel: Camera channel number (0-based)
            stream_type: 'main' or 'sub'

        Returns:
            RTSP URL
        """
        # Reolink NVR RTSP format:
        # rtsp://username:password@nvr_ip:port//h264Preview_0X_main
        # where X is channel number (01, 02, etc.)
        stream_path = "main" if stream_type == "main" else "sub"
        channel_str = str(channel + 1).zfill(2)

        return f"rtsp://{self.username}:{self.password}@{self.ip}:{self.port}//h264Preview_{channel_str}_{stream_path}"

    def add_camera_to_system(self, channel: int, name: str, stream_type: str = 'sub'):
        """
        Add NVR camera to the system

        Args:
            channel: Camera channel
            name: Camera name
            stream_type: Stream type

        Returns:
            Camera stream URL
        """
        stream_url = self.get_camera_stream(channel, stream_type)
        self.cameras[name] = {
            'channel': channel,
            'stream_url': stream_url,
            'name': name
        }

        logger.info(f"Added NVR camera: {name} (Channel {channel})")
        return stream_url


class ReolinkIntegration:
    """
    Complete Reolink integration supporting both standalone cameras and NVR
    """

    def __init__(self):
        """Initialize Reolink integration"""
        self.standalone_cameras = {}
        self.nvr = None
        self.nvr_cameras = {}

    def add_standalone_camera(self, camera_id: str, ip: str, username: str,
                             password: str, stream_type: str = 'sub'):
        """Add standalone Reolink camera"""
        camera = ReolinkCamera(ip, username, password, stream_type=stream_type, camera_name=camera_id)

        if camera.test_connection():
            self.standalone_cameras[camera_id] = camera
            logger.info(f"Added standalone camera: {camera_id}")
            return camera.get_rtsp_url()
        else:
            logger.error(f"Failed to connect to camera: {camera_id}")
            return None

    def add_nvr(self, ip: str, username: str, password: str):
        """Add Reolink NVR"""
        self.nvr = ReolinkNVR(ip, username, password)

        # Auto-discover cameras
        cameras = self.nvr.discover_cameras()

        for cam_info in cameras:
            channel = cam_info['channel']
            name = cam_info['name']
            stream_url = self.nvr.add_camera_to_system(channel, name)
            self.nvr_cameras[name] = stream_url

        logger.info(f"Added NVR with {len(cameras)} cameras")
        return self.nvr_cameras

    def get_all_streams(self) -> Dict[str, str]:
        """Get all camera streams (standalone + NVR)"""
        streams = {}

        # Add standalone cameras
        for cam_id, camera in self.standalone_cameras.items():
            streams[cam_id] = camera.get_rtsp_url()

        # Add NVR cameras
        streams.update(self.nvr_cameras)

        return streams

    def get_camera_ai_capabilities(self, camera_id: str) -> Dict:
        """
        Get AI detection capabilities of a camera

        Args:
            camera_id: Camera identifier

        Returns:
            Dict with AI capabilities
        """
        if camera_id in self.standalone_cameras:
            camera = self.standalone_cameras[camera_id]
            return camera.get_ai_detection_status()

        return {'person_detection': False, 'vehicle_detection': False, 'animal_detection': False}

    def use_camera_ai_signals(self, camera_id: str) -> bool:
        """
        Check if we should use camera's built-in AI signals

        Args:
            camera_id: Camera identifier

        Returns:
            True if camera has AI capabilities enabled
        """
        capabilities = self.get_camera_ai_capabilities(camera_id)
        return any(capabilities.values())
