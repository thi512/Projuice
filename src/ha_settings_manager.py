"""
Home Assistant Settings Manager
Manages Home Assistant MQTT configuration with persistent storage
"""
import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class HomeAssistantSettingsManager:
    """Manage Home Assistant MQTT settings"""

    def __init__(self, settings_file='data/ha_settings.json'):
        """
        Initialize HA settings manager

        Args:
            settings_file: Path to persistent settings file
        """
        self.settings_file = settings_file
        self.settings = self._get_default_settings()

        # Load saved settings
        self.load_settings()

    def _get_default_settings(self) -> Dict:
        """Get default settings"""
        return {
            'enabled': False,
            'mqtt': {
                'broker': 'localhost',
                'port': 1883,
                'username': '',
                'password': '',
                'client_id': 'ai_camera_system',
                'keepalive': 60,
                'qos': 1
            },
            'auto_discovery': True,
            'device_name': 'AI Camera System',
            'publish': {
                'person_detection': True,
                'vehicle_detection': True,
                'motion_detection': True,
                'anomaly_detection': True,
                'speed_data': True,
                'activity_level': True,
                'statistics': True,
                'license_plates': True,
                'face_recognition': True
            },
            'topics': {
                'base': 'homeassistant/ai_camera',
                'person': 'person_detected',
                'vehicle': 'vehicle_detected',
                'motion': 'motion',
                'anomaly': 'anomaly',
                'speed': 'vehicle_speed',
                'activity': 'activity_level',
                'stats': 'statistics',
                'license_plate': 'license_plate',
                'face': 'face_detected'
            },
            'update_interval': 30,  # seconds
            'retain_messages': False
        }

    def load_settings(self):
        """Load settings from JSON file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)

                # Merge with defaults (in case new settings were added)
                self._deep_merge(self.settings, loaded)

                logger.info(f"Loaded Home Assistant settings from {self.settings_file}")

            except Exception as e:
                logger.error(f"Failed to load HA settings: {e}")
        else:
            logger.info("No saved Home Assistant settings found, using defaults")

    def save_settings(self) -> bool:
        """
        Save settings to JSON file

        Returns:
            True if successful
        """
        try:
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)

            # Add timestamp
            self.settings['last_updated'] = datetime.now().isoformat()

            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)

            logger.info(f"Saved Home Assistant settings to {self.settings_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save HA settings: {e}")
            return False

    def _deep_merge(self, base: Dict, updates: Dict):
        """Deep merge updates into base dictionary"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def get_settings(self) -> Dict:
        """Get current settings"""
        return self.settings.copy()

    def update_settings(self, updates: Dict) -> bool:
        """
        Update settings

        Args:
            updates: Dictionary of updates

        Returns:
            True if successful
        """
        try:
            self._deep_merge(self.settings, updates)
            return self.save_settings()

        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False

    def test_connection(self) -> Dict:
        """
        Test MQTT connection

        Returns:
            Dictionary with test results
        """
        result = {
            'success': False,
            'message': '',
            'broker_reachable': False,
            'authenticated': False
        }

        try:
            import paho.mqtt.client as mqtt

            # Test connection
            client = mqtt.Client(client_id=self.settings['mqtt']['client_id'])

            if self.settings['mqtt']['username']:
                client.username_pw_set(
                    self.settings['mqtt']['username'],
                    self.settings['mqtt']['password']
                )

            # Connection callback
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    result['success'] = True
                    result['broker_reachable'] = True
                    result['authenticated'] = True
                    result['message'] = 'Successfully connected to MQTT broker'
                else:
                    result['broker_reachable'] = True
                    result['message'] = f'Connection failed: {mqtt.connack_string(rc)}'

            client.on_connect = on_connect

            # Try to connect
            client.connect(
                self.settings['mqtt']['broker'],
                self.settings['mqtt']['port'],
                self.settings['mqtt']['keepalive']
            )

            client.loop_start()
            import time
            time.sleep(2)  # Wait for connection
            client.loop_stop()
            client.disconnect()

        except ImportError:
            result['message'] = 'paho-mqtt library not installed'
        except Exception as e:
            result['message'] = f'Connection test failed: {str(e)}'

        return result

    def get_entity_configurations(self) -> List[Dict]:
        """
        Get Home Assistant entity configurations for auto-discovery

        Returns:
            List of entity configurations
        """
        entities = []
        base_topic = self.settings['topics']['base']
        device_name = self.settings['device_name']

        # Device info
        device = {
            'identifiers': ['ai_camera_system'],
            'name': device_name,
            'model': 'AI Camera System',
            'manufacturer': 'Custom'
        }

        if self.settings['publish']['person_detection']:
            entities.append({
                'type': 'binary_sensor',
                'name': 'Person Detected',
                'state_topic': f"{base_topic}/{self.settings['topics']['person']}",
                'device_class': 'motion',
                'device': device
            })

        if self.settings['publish']['vehicle_detection']:
            entities.append({
                'type': 'binary_sensor',
                'name': 'Vehicle Detected',
                'state_topic': f"{base_topic}/{self.settings['topics']['vehicle']}",
                'device_class': 'motion',
                'device': device
            })

        if self.settings['publish']['motion_detection']:
            entities.append({
                'type': 'binary_sensor',
                'name': 'Motion',
                'state_topic': f"{base_topic}/{self.settings['topics']['motion']}",
                'device_class': 'motion',
                'device': device
            })

        if self.settings['publish']['speed_data']:
            entities.append({
                'type': 'sensor',
                'name': 'Vehicle Speed',
                'state_topic': f"{base_topic}/{self.settings['topics']['speed']}",
                'unit_of_measurement': 'km/h',
                'device': device
            })

        if self.settings['publish']['activity_level']:
            entities.append({
                'type': 'sensor',
                'name': 'Activity Level',
                'state_topic': f"{base_topic}/{self.settings['topics']['activity']}",
                'device': device
            })

        return entities

    def export_config(self) -> str:
        """
        Export configuration for Home Assistant configuration.yaml

        Returns:
            YAML-formatted string
        """
        lines = [
            '# AI Camera System - Home Assistant Configuration',
            '',
            'mqtt:',
            f"  broker: {self.settings['mqtt']['broker']}",
            f"  port: {self.settings['mqtt']['port']}",
        ]

        if self.settings['mqtt']['username']:
            lines.append(f"  username: {self.settings['mqtt']['username']}")
            lines.append('  password: !secret ai_camera_mqtt_password')

        lines.extend([
            '',
            '# Auto-discovered entities will appear automatically',
            f"# Base topic: {self.settings['topics']['base']}",
            ''
        ])

        return '\n'.join(lines)
