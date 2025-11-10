# API Documentation - Home AI ML Camera System

## Overview

This document provides comprehensive API documentation for the Home AI ML Camera System. All endpoints are RESTful and return JSON responses.

**Base URL:** `http://<host>:<port>` (default: `http://localhost:5000`)

**API Version:** 1.0

---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Response Formats](#common-response-formats)
3. [Camera Discovery API](#camera-discovery-api)
4. [Camera Management API](#camera-management-api)
5. [Entity Labeling API](#entity-labeling-api)
6. [Home Assistant API](#home-assistant-api)
7. [Analytics API](#analytics-api)
8. [Speed Monitoring API](#speed-monitoring-api)
9. [Chatbot Query API](#chatbot-query-api)
10. [System API](#system-api)
11. [WebSocket Events](#websocket-events)
12. [Error Codes](#error-codes)
13. [Code Examples](#code-examples)

---

## Authentication

Currently, the API does not require authentication. **This is suitable for trusted local networks only.**

**Production Recommendations:**
- Implement JWT or session-based authentication
- Use HTTPS with reverse proxy (nginx)
- Add API key authentication
- Implement rate limiting

---

## Common Response Formats

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

### HTTP Status Codes
- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Camera Discovery API

### 1. Discover Cameras on Network

Scan network for IP cameras using multiple discovery methods (ONVIF, port scanning).

**Endpoint:** `POST /api/cameras/discover`

**Request Body:**
```json
{
  "network_range": "192.168.1.0/24"
}
```

**Parameters:**
- `network_range` (string, optional): Network range in CIDR notation. If omitted, only ONVIF discovery is performed.

**Response:**
```json
{
  "success": true,
  "cameras": [
    {
      "ip": "192.168.1.110",
      "port": 80,
      "protocol": "reolink",
      "name": "Reolink Camera (192.168.1.110)",
      "manufacturer": "Reolink",
      "model": "RLC-810A",
      "rtsp_urls": [
        {
          "name": "Main Stream",
          "url": "rtsp://192.168.1.110:554/h264Preview_01_main",
          "quality": "high"
        },
        {
          "name": "Sub Stream",
          "url": "rtsp://192.168.1.110:554/h264Preview_01_sub",
          "quality": "low"
        }
      ],
      "capabilities": {
        "pan_tilt": false,
        "zoom": false,
        "audio": true,
        "motion_detection": true,
        "night_vision": true,
        "onvif": true,
        "rtsp": true,
        "web_interface": true
      },
      "web_interface": "http://192.168.1.110",
      "onvif_service": "http://192.168.1.110/onvif/device_service"
    }
  ],
  "count": 1
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/cameras/discover \
  -H "Content-Type: application/json" \
  -d '{"network_range": "192.168.1.0/24"}'
```

---

### 2. Discover NVR Cameras

Discover all cameras connected to an NVR (Network Video Recorder).

**Endpoint:** `POST /api/cameras/discover/nvr`

**Request Body:**
```json
{
  "nvr_ip": "192.168.1.100",
  "nvr_port": 80,
  "username": "admin",
  "password": "password123",
  "nvr_type": "auto"
}
```

**Parameters:**
- `nvr_ip` (string, required): NVR IP address
- `nvr_port` (integer, optional): NVR HTTP port (default: 80)
- `username` (string, optional): Authentication username
- `password` (string, optional): Authentication password
- `nvr_type` (string, optional): NVR type - `auto`, `reolink`, `hikvision`, `dahua`, `onvif` (default: `auto`)

**Supported NVR Types:**
- **Reolink**: Full support with channel names and online status
- **Hikvision**: ISAPI protocol support
- **Dahua**: CGI API support
- **Generic ONVIF**: Fallback for unknown NVRs

**Response:**
```json
{
  "success": true,
  "cameras": [
    {
      "ip": "192.168.1.100",
      "port": 554,
      "protocol": "reolink_nvr",
      "nvr_ip": "192.168.1.100",
      "nvr_port": 80,
      "channel": 1,
      "name": "Front Door (NVR 192.168.1.100 Ch1)",
      "manufacturer": "Reolink",
      "model": "NVR Channel",
      "online": true,
      "nvr_model": "RLN8-410",
      "rtsp_urls": [
        {
          "name": "Main Stream",
          "url": "rtsp://192.168.1.100:554/h264Preview_01_main",
          "quality": "high"
        },
        {
          "name": "Sub Stream",
          "url": "rtsp://192.168.1.100:554/h264Preview_01_sub",
          "quality": "low"
        }
      ],
      "capabilities": {
        "rtsp": true,
        "nvr_channel": true
      }
    }
  ],
  "count": 4,
  "nvr_ip": "192.168.1.100",
  "nvr_type": "reolink"
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/cameras/discover/nvr \
  -H "Content-Type: application/json" \
  -d '{
    "nvr_ip": "192.168.1.100",
    "username": "admin",
    "password": "password123",
    "nvr_type": "auto"
  }'
```

---

### 3. Get Network Interfaces

Get available network interfaces for scanning.

**Endpoint:** `GET /api/cameras/interfaces`

**Response:**
```json
{
  "interfaces": [
    {
      "name": "eth0",
      "ip": "192.168.1.50",
      "netmask": "255.255.255.0",
      "network": "192.168.1.0/24",
      "cidr": "192.168.1.0/24"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:5000/api/cameras/interfaces
```

---

## Camera Management API

### 4. Get All Cameras

Retrieve all configured cameras.

**Endpoint:** `GET /api/cameras`

**Response:**
```json
{
  "cameras": [
    {
      "id": "cam_0_192_168_1_110",
      "ip": "192.168.1.110",
      "name": "Front Door Camera",
      "protocol": "reolink",
      "enabled": true,
      "settings": {
        "rotation": 0,
        "flip_horizontal": false,
        "flip_vertical": false,
        "resolution": "1080p",
        "fps": 30,
        "quality": "high"
      },
      "added_at": "2025-11-10T08:00:00",
      "updated_at": "2025-11-10T09:30:00"
    }
  ]
}
```

---

### 5. Add Camera

Add a new camera to the system.

**Endpoint:** `POST /api/cameras`

**Request Body:**
```json
{
  "ip": "192.168.1.110",
  "port": 80,
  "name": "Front Door Camera",
  "protocol": "reolink",
  "manufacturer": "Reolink",
  "model": "RLC-810A",
  "rtsp_urls": [
    {
      "name": "Main Stream",
      "url": "rtsp://admin:password@192.168.1.110:554/h264Preview_01_main",
      "quality": "high"
    }
  ],
  "settings": {
    "rotation": 0,
    "flip_horizontal": false,
    "resolution": "1080p",
    "fps": 30
  }
}
```

**Response:**
```json
{
  "success": true,
  "camera_id": "cam_0_192_168_1_110"
}
```

---

### 6. Update Camera

Update camera settings.

**Endpoint:** `PUT /api/cameras/<camera_id>`

**Request Body:**
```json
{
  "name": "Main Entrance Camera",
  "enabled": true,
  "settings": {
    "rotation": 90,
    "fps": 25
  }
}
```

**Response:**
```json
{
  "success": true
}
```

---

### 7. Delete Camera

Remove a camera from the system.

**Endpoint:** `DELETE /api/cameras/<camera_id>`

**Response:**
```json
{
  "success": true
}
```

---

### 8. Get Homepage Cameras

Get cameras configured for homepage display.

**Endpoint:** `GET /api/cameras/homepage`

**Response:**
```json
{
  "cameras": [
    {
      "id": "cam_0_192_168_1_110",
      "name": "Front Door Camera",
      ...
    }
  ],
  "camera_ids": ["cam_0_192_168_1_110", "cam_1_192_168_1_111"]
}
```

---

### 9. Set Homepage Cameras

Configure which cameras appear on homepage.

**Endpoint:** `POST /api/cameras/homepage`

**Request Body:**
```json
{
  "camera_ids": ["cam_0_192_168_1_110", "cam_1_192_168_1_111"]
}
```

**Response:**
```json
{
  "success": true
}
```

---

### 10. Test Camera Connection

Test connectivity to a camera.

**Endpoint:** `POST /api/cameras/<camera_id>/test`

**Request Body:**
```json
{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "rtsp_tested": true,
  "http_tested": true,
  "message": "Successfully connected to Main Stream"
}
```

---

## Entity Labeling API

### 11. Get Unlabeled Faces

Retrieve faces that appear frequently but haven't been labeled.

**Endpoint:** `GET /api/entities/unlabeled/faces`

**Query Parameters:**
- `min_appearances` (integer, optional): Minimum number of appearances (default: 3)
- `days` (integer, optional): Look back period in days (default: 30)

**Response:**
```json
{
  "faces": [
    {
      "person_id": "Unknown_1",
      "appearances": 15,
      "first_seen": "2025-10-10T08:00:00",
      "last_seen": "2025-11-10T09:30:00",
      "type": "face"
    },
    {
      "person_id": "Unknown_2",
      "appearances": 8,
      "first_seen": "2025-11-01T14:00:00",
      "last_seen": "2025-11-10T10:15:00",
      "type": "face"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:5000/api/entities/unlabeled/faces?min_appearances=5&days=30"
```

---

### 12. Get Unlabeled Vehicles

Retrieve vehicles that appear frequently.

**Endpoint:** `GET /api/entities/unlabeled/vehicles`

**Query Parameters:**
- `min_appearances` (integer, optional): Minimum number of appearances (default: 5)
- `days` (integer, optional): Look back period in days (default: 30)

**Response:**
```json
{
  "vehicles": [
    {
      "identifier": "ABC123",
      "type": "vehicle",
      "vehicle_type": "car",
      "color": "blue",
      "appearances": 12,
      "first_seen": "2025-10-15T07:00:00",
      "last_seen": "2025-11-10T08:45:00",
      "confidence": 0.89,
      "label": null,
      "is_labeled": false
    }
  ]
}
```

---

### 13. Label Face

Assign a name to a detected face.

**Endpoint:** `POST /api/entities/label/face`

**Request Body:**
```json
{
  "person_id": "Unknown_1",
  "name": "John Smith",
  "notes": "Regular visitor, arrives weekdays 8-9 AM"
}
```

**Response:**
```json
{
  "success": true
}
```

**Note:** This updates ALL historical records with this person_id to use the new name.

---

### 14. Label Vehicle

Assign a label to a vehicle (by license plate).

**Endpoint:** `POST /api/entities/label/vehicle`

**Request Body:**
```json
{
  "identifier": "ABC123",
  "label": "My Car",
  "notes": "Honda Civic - Personal vehicle"
}
```

**Response:**
```json
{
  "success": true
}
```

---

### 15. Get Labeled Entities

Retrieve all labeled entities.

**Endpoint:** `GET /api/entities/labeled`

**Query Parameters:**
- `type` (string, optional): Filter by type - `all`, `face`, `vehicle` (default: `all`)

**Response:**
```json
{
  "entities": [
    {
      "name": "John Smith",
      "type": "face",
      "appearances": 45,
      "last_seen": "2025-11-10T09:30:00"
    },
    {
      "identifier": "ABC123",
      "type": "vehicle",
      "label": "My Car",
      "notes": "Honda Civic",
      "vehicle_type": "car",
      "color": "blue",
      "appearances": 12,
      "last_seen": "2025-11-10T08:45:00"
    }
  ]
}
```

---

### 16. Remove Entity Label

Remove a label from an entity.

**Endpoint:** `DELETE /api/entities/<entity_type>/<identifier>`

**Parameters:**
- `entity_type`: `face` or `vehicle`
- `identifier`: Entity identifier (person name or plate number)

**Response:**
```json
{
  "success": true
}
```

**Example:**
```bash
curl -X DELETE http://localhost:5000/api/entities/face/John%20Smith
```

---

### 17. Get Entity History

Get appearance history for an entity.

**Endpoint:** `GET /api/entities/<entity_type>/<identifier>/history`

**Parameters:**
- `entity_type`: `face` or `vehicle`
- `identifier`: Entity identifier
- `days` (query param, optional): Number of days (default: 30)

**Response:**
```json
{
  "history": [
    {
      "timestamp": "2025-11-10T09:30:00",
      "confidence": 0.95,
      "is_unusual": false,
      "camera_id": "cam_0_192_168_1_110"
    },
    {
      "timestamp": "2025-11-10T08:00:00",
      "confidence": 0.92,
      "is_unusual": false,
      "camera_id": "cam_0_192_168_1_110"
    }
  ]
}
```

---

## Home Assistant API

### 18. Get Home Assistant Settings

Retrieve current Home Assistant MQTT settings.

**Endpoint:** `GET /api/ha/settings`

**Response:**
```json
{
  "enabled": true,
  "mqtt": {
    "broker": "192.168.1.100",
    "port": 1883,
    "username": "mqtt_user",
    "password": "********",
    "client_id": "ai_camera_system",
    "keepalive": 60,
    "qos": 1
  },
  "auto_discovery": true,
  "device_name": "AI Camera System",
  "publish": {
    "person_detection": true,
    "vehicle_detection": true,
    "motion_detection": true,
    "anomaly_detection": true,
    "speed_data": true,
    "activity_level": true,
    "statistics": true,
    "license_plates": true,
    "face_recognition": true
  },
  "topics": {
    "base": "homeassistant/ai_camera",
    "person": "person_detected",
    "vehicle": "vehicle_detected",
    "motion": "motion",
    "anomaly": "anomaly",
    "speed": "vehicle_speed",
    "activity": "activity_level",
    "stats": "statistics",
    "license_plate": "license_plate",
    "face": "face_detected"
  },
  "update_interval": 30,
  "retain_messages": false,
  "last_updated": "2025-11-10T10:00:00"
}
```

---

### 19. Update Home Assistant Settings

Update Home Assistant MQTT configuration.

**Endpoint:** `POST /api/ha/settings`

**Request Body:**
```json
{
  "enabled": true,
  "mqtt": {
    "broker": "192.168.1.100",
    "port": 1883,
    "username": "mqtt_user",
    "password": "secure_password"
  },
  "publish": {
    "person_detection": true,
    "vehicle_detection": true,
    "speed_data": false
  }
}
```

**Response:**
```json
{
  "success": true
}
```

---

### 20. Test MQTT Connection

Test connection to MQTT broker.

**Endpoint:** `POST /api/ha/test`

**Response:**
```json
{
  "success": true,
  "broker_reachable": true,
  "authenticated": true,
  "message": "Successfully connected to MQTT broker"
}
```

**Error Response:**
```json
{
  "success": false,
  "broker_reachable": false,
  "authenticated": false,
  "message": "Connection failed: Connection refused"
}
```

---

### 21. Get Home Assistant Entities

Get auto-discovery entity configurations.

**Endpoint:** `GET /api/ha/entities`

**Response:**
```json
{
  "entities": [
    {
      "type": "binary_sensor",
      "name": "Person Detected",
      "state_topic": "homeassistant/ai_camera/person_detected",
      "device_class": "motion",
      "device": {
        "identifiers": ["ai_camera_system"],
        "name": "AI Camera System",
        "model": "AI Camera System",
        "manufacturer": "Custom"
      }
    },
    {
      "type": "sensor",
      "name": "Vehicle Speed",
      "state_topic": "homeassistant/ai_camera/vehicle_speed",
      "unit_of_measurement": "km/h",
      "device": {...}
    }
  ]
}
```

---

### 22. Export Home Assistant Config

Export YAML configuration for Home Assistant.

**Endpoint:** `GET /api/ha/export`

**Response:**
```json
{
  "config": "# AI Camera System - Home Assistant Configuration\n\nmqtt:\n  broker: 192.168.1.100\n  port: 1883\n  username: mqtt_user\n  password: !secret ai_camera_mqtt_password\n\n# Auto-discovered entities will appear automatically\n# Base topic: homeassistant/ai_camera\n"
}
```

---

## Analytics API

### 23. Get System Statistics

Get overall system statistics.

**Endpoint:** `GET /api/stats`

**Response:**
```json
{
  "total_detections": 1523,
  "persons_detected": 342,
  "vehicles_detected": 187,
  "faces_recognized": 89,
  "plates_read": 145,
  "anomalies_detected": 12,
  "uptime": "5 days, 3:24:15",
  "database_size_mb": 45.6
}
```

---

### 24. Get Hourly Analytics

Get detection counts by hour.

**Endpoint:** `GET /api/analytics/hourly`

**Query Parameters:**
- `days` (integer, optional): Number of days (default: 7)

**Response:**
```json
{
  "hourly_data": [
    {"hour": 0, "count": 5},
    {"hour": 1, "count": 2},
    ...
    {"hour": 23, "count": 8}
  ]
}
```

---

### 25. Get Activity Levels

Get activity classification over time.

**Endpoint:** `GET /api/analytics/activity`

**Response:**
```json
{
  "current_activity": "normal",
  "activity_history": [
    {"timestamp": "2025-11-10T09:00:00", "level": "low", "count": 2},
    {"timestamp": "2025-11-10T10:00:00", "level": "normal", "count": 5},
    {"timestamp": "2025-11-10T11:00:00", "level": "high", "count": 15}
  ]
}
```

---

### 26. Get Frequent Objects

Get most frequently detected objects.

**Endpoint:** `GET /api/analytics/frequent-objects`

**Query Parameters:**
- `days` (integer, optional): Number of days (default: 30)
- `limit` (integer, optional): Number of results (default: 10)

**Response:**
```json
{
  "objects": [
    {"type": "person", "count": 342, "percentage": 45.2},
    {"type": "car", "count": 187, "percentage": 24.7},
    {"type": "truck", "count": 45, "percentage": 5.9}
  ]
}
```

---

## Speed Monitoring API

### 27. Get Speed Statistics

Get vehicle speed statistics.

**Endpoint:** `GET /api/speed/stats`

**Response:**
```json
{
  "average_speed": 38.5,
  "max_speed": 75.2,
  "min_speed": 15.0,
  "total_vehicles": 187,
  "speed_limit": 50.0,
  "violations": 12
}
```

---

### 28. Get Speed Violations

Get vehicles exceeding speed limit.

**Endpoint:** `GET /api/speed/violations`

**Query Parameters:**
- `days` (integer, optional): Number of days (default: 7)

**Response:**
```json
{
  "violations": [
    {
      "timestamp": "2025-11-10T14:30:00",
      "speed": 75.2,
      "limit": 50.0,
      "plate": "ABC123",
      "vehicle_type": "car",
      "color": "red"
    }
  ],
  "count": 12
}
```

---

## Chatbot Query API

### 29. Query Chatbot

Ask natural language questions about detections.

**Endpoint:** `POST /api/chatbot/query`

**Request Body:**
```json
{
  "question": "How many people were detected today?",
  "conversation_id": "conv_123"
}
```

**Response:**
```json
{
  "answer": "Today, 45 people were detected. The busiest hour was between 8-9 AM with 12 detections.",
  "conversation_id": "conv_123",
  "relevant_data": {
    "total_persons": 45,
    "peak_hour": 8,
    "peak_count": 12
  }
}
```

---

### 30. Get Chat History

Get conversation history.

**Endpoint:** `GET /api/chatbot/history`

**Query Parameters:**
- `conversation_id` (string, optional): Specific conversation

**Response:**
```json
{
  "conversations": [
    {
      "id": "conv_123",
      "messages": [
        {"role": "user", "content": "How many people were detected today?"},
        {"role": "assistant", "content": "Today, 45 people were detected..."}
      ]
    }
  ]
}
```

---

### 31. Reset Chat

Clear conversation history.

**Endpoint:** `POST /api/chatbot/reset`

**Request Body:**
```json
{
  "conversation_id": "conv_123"
}
```

**Response:**
```json
{
  "success": true
}
```

---

## System API

### 32. Get System Status

Get current system status.

**Endpoint:** `GET /api/status`

**Response:**
```json
{
  "running": true,
  "recording": false,
  "detections_enabled": true,
  "motion_enabled": true,
  "uptime": "5 days, 3:24:15",
  "ai_features_enabled": true,
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 4070 Ti",
  "gpu_memory_used": "4.2 GB / 12.0 GB"
}
```

---

### 33. Get Video Feed

Get live video stream.

**Endpoint:** `GET /video_feed`

**Response:** Multipart JPEG stream

**Example (HTML):**
```html
<img src="http://localhost:5000/video_feed" />
```

---

## WebSocket Events

**Connect:** `ws://localhost:5000/socket.io/`

**Events Received:**

### 1. detection_event
```json
{
  "type": "person",
  "id": "person_123",
  "confidence": 0.95,
  "timestamp": "2025-11-10T09:30:00"
}
```

### 2. speed_event
```json
{
  "speed": 65.5,
  "plate": "ABC123",
  "is_violation": true,
  "timestamp": "2025-11-10T09:30:00"
}
```

### 3. anomaly_event
```json
{
  "type": "loitering",
  "severity": 0.8,
  "description": "Person detected in restricted area for 5 minutes",
  "timestamp": "2025-11-10T09:30:00"
}
```

### 4. stats_update
```json
{
  "total_detections": 1524,
  "persons_detected": 343,
  "vehicles_detected": 187
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `CAMERA_NOT_FOUND` | Camera ID not found in system |
| `DISCOVERY_FAILED` | Camera discovery failed |
| `NVR_CONNECTION_FAILED` | Failed to connect to NVR |
| `ENTITY_NOT_FOUND` | Entity identifier not found |
| `DATABASE_ERROR` | Database operation failed |
| `MQTT_CONNECTION_FAILED` | MQTT broker connection failed |
| `INVALID_PARAMETER` | Invalid request parameter |
| `AUTHENTICATION_FAILED` | Camera authentication failed |
| `SYSTEM_NOT_INITIALIZED` | Camera system not initialized |

---

## Code Examples

### Python

```python
import requests

# Base URL
base_url = "http://localhost:5000"

# 1. Discover NVR cameras
response = requests.post(f"{base_url}/api/cameras/discover/nvr", json={
    "nvr_ip": "192.168.1.100",
    "username": "admin",
    "password": "password",
    "nvr_type": "auto"
})
cameras = response.json()["cameras"]
print(f"Found {len(cameras)} cameras")

# 2. Add discovered camera
camera = cameras[0]
response = requests.post(f"{base_url}/api/cameras", json=camera)
camera_id = response.json()["camera_id"]
print(f"Added camera: {camera_id}")

# 3. Get unlabeled faces
response = requests.get(f"{base_url}/api/entities/unlabeled/faces", params={
    "min_appearances": 5,
    "days": 30
})
faces = response.json()["faces"]

# 4. Label a face
if faces:
    response = requests.post(f"{base_url}/api/entities/label/face", json={
        "person_id": faces[0]["person_id"],
        "name": "John Smith",
        "notes": "Regular visitor"
    })
    print(f"Labeled face: {response.json()}")

# 5. Configure Home Assistant
response = requests.post(f"{base_url}/api/ha/settings", json={
    "enabled": True,
    "mqtt": {
        "broker": "192.168.1.100",
        "port": 1883,
        "username": "mqtt_user",
        "password": "mqtt_pass"
    }
})
print(f"HA configured: {response.json()}")

# 6. Test MQTT connection
response = requests.post(f"{base_url}/api/ha/test")
result = response.json()
print(f"MQTT test: {result['message']}")
```

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const baseURL = 'http://localhost:5000';

// Discover cameras
async function discoverCameras() {
  const response = await axios.post(`${baseURL}/api/cameras/discover`, {
    network_range: '192.168.1.0/24'
  });

  console.log(`Found ${response.data.count} cameras`);
  return response.data.cameras;
}

// Get unlabeled entities
async function getUnlabeledFaces() {
  const response = await axios.get(`${baseURL}/api/entities/unlabeled/faces`, {
    params: { min_appearances: 3, days: 30 }
  });

  return response.data.faces;
}

// Label face
async function labelFace(personId, name, notes = '') {
  const response = await axios.post(`${baseURL}/api/entities/label/face`, {
    person_id: personId,
    name: name,
    notes: notes
  });

  return response.data.success;
}

// WebSocket connection
const io = require('socket.io-client');
const socket = io('http://localhost:5000');

socket.on('detection_event', (data) => {
  console.log('Detection:', data);
});

socket.on('speed_event', (data) => {
  console.log('Speed event:', data);
});
```

### cURL

```bash
# Discover NVR cameras
curl -X POST http://localhost:5000/api/cameras/discover/nvr \
  -H "Content-Type: application/json" \
  -d '{
    "nvr_ip": "192.168.1.100",
    "username": "admin",
    "password": "password"
  }'

# Get all cameras
curl http://localhost:5000/api/cameras

# Label a face
curl -X POST http://localhost:5000/api/entities/label/face \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "Unknown_1",
    "name": "John Smith",
    "notes": "Regular visitor"
  }'

# Test Home Assistant
curl -X POST http://localhost:5000/api/ha/test

# Get statistics
curl http://localhost:5000/api/stats
```

---

## Rate Limiting

**Current Status:** No rate limiting implemented

**Recommendations for Production:**
- Implement rate limiting per IP: 100 requests/minute
- Implement per-endpoint limits:
  - Discovery endpoints: 10 requests/minute
  - Query endpoints: 60 requests/minute
  - Update endpoints: 30 requests/minute

---

## Versioning

**Current Version:** 1.0

Future versions will use URL versioning:
- `http://localhost:5000/api/v1/cameras`
- `http://localhost:5000/api/v2/cameras`

---

## Support

For issues or questions:
- GitHub Issues: `https://github.com/your-repo/issues`
- Documentation: `ARCHITECTURE.md`
- Configuration: `README.md`

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-10
**API Version:** 1.0
