"""
Home Assistant MQTT Integration
Publishes detection events and sensor data to Home Assistant via MQTT
"""
import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable
from threading import Thread
import time

logger = logging.getLogger(__name__)


class HomeAssistantMQTT:
    """
    Home Assistant MQTT Integration
    Auto-discovers entities and publishes sensor data
    """

    def __init__(self, broker: str, port: int = 1883, username: str = None,
                 password: str = None, device_name: str = "AI Camera System"):
        """
        Initialize Home Assistant MQTT client

        Args:
            broker: MQTT broker address
            port: MQTT port
            username: MQTT username
            password: MQTT password
            device_name: Device name for Home Assistant
        """
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.device_name = device_name
        self.client = None
        self.connected = False

        # Base topics
        self.base_topic = f"homeassistant/sensor/ai_camera"
        self.state_topic = f"{self.base_topic}/state"

        # Callbacks for commands
        self.command_callbacks = {}

        self._setup_client()

    def _setup_client(self):
        """Setup MQTT client"""
        self.client = mqtt.Client(client_id=f"ai_camera_system_{int(time.time())}")

        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self.client.will_set(
            f"{self.base_topic}/availability",
            payload="offline",
            qos=1,
            retain=True
        )

    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to Home Assistant MQTT broker")

            # Publish availability
            self.client.publish(
                f"{self.base_topic}/availability",
                "online",
                qos=1,
                retain=True
            )

            # Subscribe to command topics
            self.client.subscribe(f"{self.base_topic}/+/set")

            # Send discovery messages
            self._send_discovery_messages()
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        logger.warning("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Callback for incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode()

            logger.info(f"Received MQTT message: {topic} = {payload}")

            # Handle commands
            if "/set" in topic:
                command_type = topic.split("/")[-2]
                if command_type in self.command_callbacks:
                    self.command_callbacks[command_type](payload)

        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.publish(
                f"{self.base_topic}/availability",
                "offline",
                qos=1,
                retain=True
            )
            self.client.loop_stop()
            self.client.disconnect()

    def _send_discovery_messages(self):
        """Send MQTT discovery messages for Home Assistant"""
        device_info = {
            "identifiers": ["ai_camera_system"],
            "name": self.device_name,
            "model": "AI ML Camera System",
            "manufacturer": "Home AI"
        }

        # Person detection sensor
        self._publish_discovery("person_count", "Person Count", "sensor", {
            "state_topic": f"{self.base_topic}/person_count",
            "unit_of_measurement": "people",
            "icon": "mdi:account-multiple",
            "device": device_info
        })

        # Vehicle detection sensor
        self._publish_discovery("vehicle_count", "Vehicle Count", "sensor", {
            "state_topic": f"{self.base_topic}/vehicle_count",
            "unit_of_measurement": "vehicles",
            "icon": "mdi:car",
            "device": device_info
        })

        # Motion detection binary sensor
        self._publish_discovery("motion", "Motion Detected", "binary_sensor", {
            "state_topic": f"{self.base_topic}/motion",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device_class": "motion",
            "device": device_info
        })

        # Anomaly detection binary sensor
        self._publish_discovery("anomaly", "Anomaly Detected", "binary_sensor", {
            "state_topic": f"{self.base_topic}/anomaly",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device_class": "safety",
            "icon": "mdi:alert",
            "device": device_info
        })

        # Average vehicle speed sensor
        self._publish_discovery("vehicle_speed", "Average Vehicle Speed", "sensor", {
            "state_topic": f"{self.base_topic}/vehicle_speed",
            "unit_of_measurement": "km/h",
            "icon": "mdi:speedometer",
            "device": device_info
        })

        # Recording status
        self._publish_discovery("recording", "Recording Status", "binary_sensor", {
            "state_topic": f"{self.base_topic}/recording",
            "payload_on": "ON",
            "payload_off": "OFF",
            "device_class": "running",
            "icon": "mdi:record-rec",
            "device": device_info
        })

        # System activity level
        self._publish_discovery("activity_level", "Activity Level", "sensor", {
            "state_topic": f"{self.base_topic}/activity_level",
            "icon": "mdi:chart-line",
            "device": device_info
        })

        logger.info("Sent MQTT discovery messages to Home Assistant")

    def _publish_discovery(self, entity_id: str, name: str, component: str, config: Dict):
        """Publish discovery message for an entity"""
        topic = f"homeassistant/{component}/{self.device_name.lower().replace(' ', '_')}/{entity_id}/config"

        discovery_payload = {
            "name": name,
            "unique_id": f"ai_camera_{entity_id}",
            "availability_topic": f"{self.base_topic}/availability",
            **config
        }

        self.client.publish(topic, json.dumps(discovery_payload), qos=1, retain=True)

    def publish_person_detection(self, count: int, person_ids: List[str] = None):
        """Publish person detection event"""
        if not self.connected:
            return

        self.client.publish(f"{self.base_topic}/person_count", count)

        # Publish detailed event
        event_data = {
            "count": count,
            "person_ids": person_ids or [],
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish(f"{self.base_topic}/events/person", json.dumps(event_data))

        logger.debug(f"Published person detection: {count} people")

    def publish_vehicle_detection(self, count: int, vehicles: List[Dict] = None):
        """Publish vehicle detection event"""
        if not self.connected:
            return

        self.client.publish(f"{self.base_topic}/vehicle_count", count)

        # Publish detailed event
        event_data = {
            "count": count,
            "vehicles": vehicles or [],
            "timestamp": datetime.now().isoformat()
        }
        self.client.publish(f"{self.base_topic}/events/vehicle", json.dumps(event_data))

        logger.debug(f"Published vehicle detection: {count} vehicles")

    def publish_motion_detection(self, detected: bool):
        """Publish motion detection status"""
        if not self.connected:
            return

        payload = "ON" if detected else "OFF"
        self.client.publish(f"{self.base_topic}/motion", payload)

    def publish_anomaly_detection(self, detected: bool, anomaly_data: Dict = None):
        """Publish anomaly detection"""
        if not self.connected:
            return

        payload = "ON" if detected else "OFF"
        self.client.publish(f"{self.base_topic}/anomaly", payload)

        if detected and anomaly_data:
            self.client.publish(
                f"{self.base_topic}/events/anomaly",
                json.dumps({
                    **anomaly_data,
                    "timestamp": datetime.now().isoformat()
                })
            )

    def publish_vehicle_speed(self, average_speed: float):
        """Publish average vehicle speed"""
        if not self.connected:
            return

        self.client.publish(f"{self.base_topic}/vehicle_speed", f"{average_speed:.1f}")

    def publish_recording_status(self, is_recording: bool):
        """Publish recording status"""
        if not self.connected:
            return

        payload = "ON" if is_recording else "OFF"
        self.client.publish(f"{self.base_topic}/recording", payload)

    def publish_activity_level(self, level: str):
        """
        Publish activity level

        Args:
            level: Activity level ('quiet', 'normal', 'busy', 'very_busy')
        """
        if not self.connected:
            return

        self.client.publish(f"{self.base_topic}/activity_level", level)

    def publish_statistics(self, stats: Dict):
        """Publish comprehensive statistics"""
        if not self.connected:
            return

        self.client.publish(
            f"{self.base_topic}/statistics",
            json.dumps({
                **stats,
                "timestamp": datetime.now().isoformat()
            })
        )

    def register_command_callback(self, command_type: str, callback: Callable):
        """
        Register callback for command from Home Assistant

        Args:
            command_type: Type of command (e.g., 'recording', 'snapshot')
            callback: Function to call when command received
        """
        self.command_callbacks[command_type] = callback
        logger.info(f"Registered command callback: {command_type}")

    def publish_custom_sensor(self, sensor_name: str, value, attributes: Dict = None):
        """
        Publish custom sensor data

        Args:
            sensor_name: Sensor name
            value: Sensor value
            attributes: Additional attributes
        """
        if not self.connected:
            return

        topic = f"{self.base_topic}/{sensor_name}"
        self.client.publish(topic, str(value))

        if attributes:
            attr_topic = f"{topic}/attributes"
            self.client.publish(attr_topic, json.dumps(attributes))

    def create_automation_trigger(self, trigger_name: str, trigger_data: Dict):
        """
        Send data that can trigger Home Assistant automations

        Args:
            trigger_name: Trigger identifier
            trigger_data: Trigger data
        """
        if not self.connected:
            return

        topic = f"{self.base_topic}/triggers/{trigger_name}"
        payload = {
            **trigger_data,
            "timestamp": datetime.now().isoformat()
        }

        self.client.publish(topic, json.dumps(payload))
        logger.info(f"Published automation trigger: {trigger_name}")
