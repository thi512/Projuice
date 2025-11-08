"""
Configuration management module
"""
import yaml
import os
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Manage application configuration"""

    def __init__(self, config_file="config.yaml", env_file=".env"):
        """
        Initialize configuration

        Args:
            config_file: Path to YAML config file
            env_file: Path to .env file
        """
        self.config_file = config_file
        self.config = {}

        # Load .env file if it exists
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")

        # Load YAML config
        self._load_config()

    def _load_config(self):
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_file):
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            self._set_defaults()
            return

        try:
            with open(self.config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._set_defaults()

    def _set_defaults(self):
        """Set default configuration"""
        self.config = {
            'camera': {
                'index': 0,
                'resolution': {'width': 1280, 'height': 720},
                'fps': 30
            },
            'ml_model': {
                'type': 'yolov8n',
                'confidence_threshold': 0.5,
                'nms_threshold': 0.4,
                'device': 'cpu'
            },
            'detection': {
                'enable_object_detection': True,
                'enable_motion_detection': True,
                'enable_face_detection': False,
                'motion_threshold': 25,
                'motion_min_area': 500,
                'target_classes': ['person', 'car', 'truck', 'dog', 'cat']
            },
            'recording': {
                'save_recordings': True,
                'recordings_path': './recordings',
                'max_recording_duration': 300,
                'save_detections': True,
                'video_codec': 'mp4v'
            },
            'alerts': {
                'enable_alerts': True,
                'alert_cooldown': 60,
                'alert_types': ['motion', 'person_detected']
            },
            'web_interface': {
                'port': 5000,
                'host': '0.0.0.0',
                'enable_stream': True,
                'stream_quality': 80
            },
            'performance': {
                'process_every_n_frames': 1,
                'max_frame_queue_size': 10,
                'use_threading': True
            }
        }

    def get(self, path, default=None):
        """
        Get configuration value by path

        Args:
            path: Dot-separated path (e.g., 'camera.resolution.width')
            default: Default value if not found

        Returns:
            Configuration value or default
        """
        keys = path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, path, value):
        """
        Set configuration value by path

        Args:
            path: Dot-separated path (e.g., 'camera.fps')
            value: Value to set
        """
        keys = path.split('.')
        config = self.config

        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        config[keys[-1]] = value

    def save(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def get_camera_config(self):
        """Get camera configuration"""
        return {
            'camera_index': self.get('camera.index', 0),
            'width': self.get('camera.resolution.width', 1280),
            'height': self.get('camera.resolution.height', 720),
            'fps': self.get('camera.fps', 30)
        }

    def get_detector_config(self):
        """Get detector configuration"""
        return {
            'model_type': self.get('ml_model.type', 'yolov8n'),
            'confidence_threshold': self.get('ml_model.confidence_threshold', 0.5),
            'device': self.get('ml_model.device', 'cpu'),
            'target_classes': self.get('detection.target_classes', []),
            'enable_object_detection': self.get('detection.enable_object_detection', True),
            'enable_motion_detection': self.get('detection.enable_motion_detection', True),
            'enable_face_detection': self.get('detection.enable_face_detection', False),
            'motion_threshold': self.get('detection.motion_threshold', 25),
            'motion_min_area': self.get('detection.motion_min_area', 500)
        }

    def get_recorder_config(self):
        """Get recorder configuration"""
        return {
            'save_recordings': self.get('recording.save_recordings', True),
            'output_dir': self.get('recording.recordings_path', './recordings'),
            'max_duration': self.get('recording.max_recording_duration', 300),
            'codec': self.get('recording.video_codec', 'mp4v')
        }

    def get_web_config(self):
        """Get web interface configuration"""
        return {
            'port': self.get('web_interface.port', 5000),
            'host': self.get('web_interface.host', '0.0.0.0'),
            'enable_stream': self.get('web_interface.enable_stream', True),
            'stream_quality': self.get('web_interface.stream_quality', 80)
        }
