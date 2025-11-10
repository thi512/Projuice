"""
Camera Management System
Manages multiple cameras, their configurations, and persistent storage
"""
import json
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class CameraManager:
    """Manage multiple cameras and their configurations"""

    def __init__(self, settings_file='data/camera_settings.json'):
        """
        Initialize camera manager

        Args:
            settings_file: Path to persistent settings file
        """
        self.settings_file = settings_file
        self.cameras = []
        self.homepage_cameras = []
        self.active_camera_id = None

        # Load saved settings
        self.load_settings()

    def load_settings(self):
        """Load camera settings from JSON file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)

                self.cameras = settings.get('cameras', [])
                self.homepage_cameras = settings.get('homepage_cameras', [])
                self.active_camera_id = settings.get('active_camera_id')

                logger.info(f"Loaded {len(self.cameras)} camera(s) from {self.settings_file}")

            except Exception as e:
                logger.error(f"Failed to load camera settings: {e}")
        else:
            logger.info("No saved camera settings found")

    def save_settings(self) -> bool:
        """
        Save camera settings to JSON file

        Returns:
            True if successful
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)

            settings = {
                'cameras': self.cameras,
                'homepage_cameras': self.homepage_cameras,
                'active_camera_id': self.active_camera_id,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            logger.info(f"Saved camera settings to {self.settings_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save camera settings: {e}")
            return False

    def add_camera(self, camera: Dict) -> str:
        """
        Add a new camera

        Args:
            camera: Camera dictionary

        Returns:
            Camera ID
        """
        # Generate unique ID
        camera_id = f"cam_{len(self.cameras)}_{camera['ip'].replace('.', '_')}"
        camera['id'] = camera_id
        camera['enabled'] = True
        camera['added_at'] = datetime.now().isoformat()

        # Add default settings
        if 'settings' not in camera:
            camera['settings'] = {
                'rotation': 0,
                'flip_horizontal': False,
                'flip_vertical': False,
                'resolution': 'auto',
                'fps': 30,
                'quality': 'high'
            }

        self.cameras.append(camera)
        self.save_settings()

        logger.info(f"Added camera: {camera_id} ({camera['ip']})")
        return camera_id

    def remove_camera(self, camera_id: str) -> bool:
        """
        Remove a camera

        Args:
            camera_id: Camera ID

        Returns:
            True if successful
        """
        self.cameras = [c for c in self.cameras if c['id'] != camera_id]

        # Remove from homepage if present
        if camera_id in self.homepage_cameras:
            self.homepage_cameras.remove(camera_id)

        # Clear active camera if it was removed
        if self.active_camera_id == camera_id:
            self.active_camera_id = None

        self.save_settings()
        logger.info(f"Removed camera: {camera_id}")
        return True

    def update_camera(self, camera_id: str, updates: Dict) -> bool:
        """
        Update camera settings

        Args:
            camera_id: Camera ID
            updates: Dictionary of updates

        Returns:
            True if successful
        """
        for camera in self.cameras:
            if camera['id'] == camera_id:
                camera.update(updates)
                camera['updated_at'] = datetime.now().isoformat()
                self.save_settings()
                logger.info(f"Updated camera: {camera_id}")
                return True

        logger.warning(f"Camera not found: {camera_id}")
        return False

    def get_camera(self, camera_id: str) -> Optional[Dict]:
        """
        Get camera by ID

        Args:
            camera_id: Camera ID

        Returns:
            Camera dictionary or None
        """
        for camera in self.cameras:
            if camera['id'] == camera_id:
                return camera

        return None

    def get_all_cameras(self) -> List[Dict]:
        """
        Get all cameras

        Returns:
            List of camera dictionaries
        """
        return self.cameras

    def get_enabled_cameras(self) -> List[Dict]:
        """
        Get all enabled cameras

        Returns:
            List of enabled camera dictionaries
        """
        return [c for c in self.cameras if c.get('enabled', True)]

    def set_homepage_cameras(self, camera_ids: List[str]):
        """
        Set which cameras appear on homepage

        Args:
            camera_ids: List of camera IDs
        """
        # Validate camera IDs
        valid_ids = [c['id'] for c in self.cameras]
        self.homepage_cameras = [cid for cid in camera_ids if cid in valid_ids]

        self.save_settings()
        logger.info(f"Set homepage cameras: {self.homepage_cameras}")

    def get_homepage_cameras(self) -> List[Dict]:
        """
        Get cameras that should appear on homepage

        Returns:
            List of camera dictionaries
        """
        return [c for c in self.cameras if c['id'] in self.homepage_cameras]

    def set_active_camera(self, camera_id: str):
        """
        Set the active camera (for single-camera mode)

        Args:
            camera_id: Camera ID
        """
        if self.get_camera(camera_id):
            self.active_camera_id = camera_id
            self.save_settings()
            logger.info(f"Set active camera: {camera_id}")

    def get_active_camera(self) -> Optional[Dict]:
        """
        Get the active camera

        Returns:
            Camera dictionary or None
        """
        if self.active_camera_id:
            return self.get_camera(self.active_camera_id)

        # Return first enabled camera if no active camera set
        enabled = self.get_enabled_cameras()
        return enabled[0] if enabled else None

    def test_camera_connection(self, camera: Dict, username: str = '', password: str = '') -> Dict:
        """
        Test camera connection

        Args:
            camera: Camera dictionary
            username: Username for authentication
            password: Password for authentication

        Returns:
            Dictionary with test results
        """
        results = {
            'success': False,
            'message': '',
            'rtsp_tested': False,
            'http_tested': False
        }

        # Test RTSP if available
        if camera.get('rtsp_urls'):
            try:
                import cv2

                for rtsp_info in camera['rtsp_urls']:
                    rtsp_url = rtsp_info['url']

                    # Add authentication
                    if username and password:
                        if '://' in rtsp_url:
                            protocol, rest = rtsp_url.split('://', 1)
                            rtsp_url = f"{protocol}://{username}:{password}@{rest}"

                    cap = cv2.VideoCapture(rtsp_url)
                    if cap.isOpened():
                        ret, frame = cap.read()
                        cap.release()

                        if ret:
                            results['success'] = True
                            results['rtsp_tested'] = True
                            results['message'] = f"Successfully connected to {rtsp_info['name']}"
                            break

            except Exception as e:
                results['message'] = f"RTSP test failed: {str(e)}"

        # Test HTTP if available
        if camera.get('web_interface') and not results['success']:
            try:
                import requests

                url = camera['web_interface']
                if username and password:
                    response = requests.get(url, auth=(username, password), timeout=5, verify=False)
                else:
                    response = requests.get(url, timeout=5, verify=False)

                if response.status_code == 200 or response.status_code == 401:
                    results['success'] = True
                    results['http_tested'] = True
                    results['message'] = "Camera web interface accessible"

            except Exception as e:
                results['message'] = f"HTTP test failed: {str(e)}"

        if not results['success'] and not results['message']:
            results['message'] = "No testable connection methods available"

        return results

    def get_camera_settings_schema(self) -> Dict:
        """
        Get schema for camera settings

        Returns:
            JSON schema for camera settings
        """
        return {
            'type': 'object',
            'properties': {
                'rotation': {
                    'type': 'integer',
                    'enum': [0, 90, 180, 270],
                    'description': 'Rotation angle in degrees'
                },
                'flip_horizontal': {
                    'type': 'boolean',
                    'description': 'Flip image horizontally'
                },
                'flip_vertical': {
                    'type': 'boolean',
                    'description': 'Flip image vertically'
                },
                'resolution': {
                    'type': 'string',
                    'description': 'Video resolution (auto, 1080p, 720p, 480p)'
                },
                'fps': {
                    'type': 'integer',
                    'minimum': 1,
                    'maximum': 60,
                    'description': 'Frames per second'
                },
                'quality': {
                    'type': 'string',
                    'enum': ['low', 'medium', 'high'],
                    'description': 'Stream quality'
                },
                'detection_zones': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'polygon': {'type': 'array'}
                        }
                    },
                    'description': 'Custom detection zones'
                },
                'schedule': {
                    'type': 'object',
                    'properties': {
                        'enabled': {'type': 'boolean'},
                        'active_hours': {'type': 'array'}
                    },
                    'description': 'Recording schedule'
                }
            }
        }

    def export_settings(self) -> str:
        """
        Export camera settings as JSON string

        Returns:
            JSON string of all settings
        """
        settings = {
            'cameras': self.cameras,
            'homepage_cameras': self.homepage_cameras,
            'active_camera_id': self.active_camera_id,
            'exported_at': datetime.now().isoformat()
        }

        return json.dumps(settings, indent=2)

    def import_settings(self, json_str: str) -> bool:
        """
        Import camera settings from JSON string

        Args:
            json_str: JSON string of settings

        Returns:
            True if successful
        """
        try:
            settings = json.loads(json_str)

            if 'cameras' in settings:
                self.cameras = settings['cameras']
            if 'homepage_cameras' in settings:
                self.homepage_cameras = settings['homepage_cameras']
            if 'active_camera_id' in settings:
                self.active_camera_id = settings['active_camera_id']

            self.save_settings()
            logger.info("Camera settings imported successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False
