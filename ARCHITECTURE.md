# Home AI ML Camera System - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Core Components](#core-components)
4. [AI/ML Pipeline](#aiml-pipeline)
5. [Data Flow](#data-flow)
6. [API Architecture](#api-architecture)
7. [Database Schema](#database-schema)
8. [Configuration System](#configuration-system)
9. [Integration Points](#integration-points)
10. [Deployment Architecture](#deployment-architecture)

---

## System Overview

This is a professional AI-powered surveillance and camera monitoring system built with Python, leveraging state-of-the-art deep learning models for real-time object detection, face recognition, license plate recognition (LPR), and behavioral analysis.

### Technology Stack

**Core Technologies:**
- **Python 3.12+**: Primary language
- **CUDA 12.1+**: GPU acceleration (RTX 4070 Ti optimized)
- **OpenCV 4.8+**: Computer vision operations
- **Flask + SocketIO**: Web server and real-time communication
- **SQLAlchemy**: Database ORM
- **SQLite**: Persistent storage

**AI/ML Framework Stack:**
- **YOLOv11 (Ultralytics)**: Real-time object detection
- **DeepFace**: Face recognition and analysis
- **EasyOCR + PyTorch**: License plate recognition
- **TensorFlow 2.15**: Additional ML operations
- **scikit-learn**: Behavioral pattern analysis

**Network & Integration:**
- **ONVIF Protocol**: Camera discovery and control
- **RTSP**: Video streaming
- **MQTT (paho-mqtt)**: Home Assistant integration
- **HTTP/REST**: API endpoints

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Web UI      │  │  REST API    │  │  WebSocket   │             │
│  │  (Flask)     │  │  (31 endpoints) │  │  (Real-time) │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                              │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Enhanced Web Server (enhanced_web_server.py)               │    │
│  │  - Camera Management API                                    │    │
│  │  - Entity Labeling API                                      │    │
│  │  - Home Assistant API                                       │    │
│  │  - Analytics API                                            │    │
│  │  - Chatbot Query Engine                                     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │ Camera Manager │  │ Entity Labeling  │  │ HA Settings Mgr  │   │
│  │ (camera_       │  │ (entity_         │  │ (ha_settings_    │   │
│  │  manager.py)   │  │  labeling.py)    │  │  manager.py)     │   │
│  └────────────────┘  └──────────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                       CORE PROCESSING LAYER                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Enhanced Camera System (enhanced_camera_system.py)         │    │
│  │  - Video capture and processing                             │    │
│  │  - AI/ML pipeline orchestration                             │    │
│  │  - Multi-threading management                               │    │
│  │  - Event processing and recording                           │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         AI/ML LAYER                                 │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐   │
│  │ YOLOv11      │  │ Face AI        │  │ License Plate        │   │
│  │ Detection    │  │ Recognition    │  │ Recognition (LPR)    │   │
│  │ (yolo_       │  │ (face_         │  │ (lpr_system.py)      │   │
│  │  detector.py)│  │  recognition   │  │                      │   │
│  │              │  │  _system.py)   │  │                      │   │
│  └──────────────┘  └────────────────┘  └──────────────────────┘   │
│                                                                     │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐   │
│  │ Behavioral   │  │ Speed          │  │ Anomaly Detection    │   │
│  │ Analysis     │  │ Estimation     │  │ (anomaly_detector    │   │
│  │ (behavioral  │  │ (speed_        │  │  .py)                │   │
│  │  analysis.py)│  │  estimator.py) │  │                      │   │
│  └──────────────┘  └────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      NETWORK & DISCOVERY LAYER                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  Camera Discovery (camera_discovery.py)                     │    │
│  │  - ONVIF WS-Discovery                                       │    │
│  │  - Network scanning                                         │    │
│  │  - NVR Integration:                                         │    │
│  │    • Reolink NVR API                                        │    │
│  │    • Hikvision ISAPI                                        │    │
│  │    • Dahua CGI API                                          │    │
│  │    • Generic ONVIF NVR                                      │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      PERSISTENCE LAYER                              │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐   │
│  │ SQLite DB    │  │ JSON Settings  │  │ Email Reports        │   │
│  │ (database.py)│  │ - camera_      │  │ (email_reporter.py)  │   │
│  │              │  │   settings.json│  │                      │   │
│  │  Tables:     │  │ - ha_settings  │  │                      │   │
│  │  • detections│  │   .json        │  │                      │   │
│  │  • person_   │  │ - speed_       │  │                      │   │
│  │    appearances│  │   calibration  │  │                      │   │
│  │  • license_  │  │   .json        │  │                      │   │
│  │    plates    │  │                │  │                      │   │
│  │  • vehicle_  │  │                │  │                      │   │
│  │    records   │  │                │  │                      │   │
│  │  • anomalies │  │                │  │                      │   │
│  └──────────────┘  └────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      INTEGRATION LAYER                              │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐   │
│  │ Home Assistant       │  │ Email Notifications              │   │
│  │ (MQTT Discovery)     │  │ (SMTP)                           │   │
│  └──────────────────────┘  └──────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      HARDWARE LAYER                                 │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────────┐   │
│  │ IP Cameras   │  │ NVR Systems    │  │ RTX 4070 Ti GPU      │   │
│  │ (RTSP/ONVIF) │  │ (Multi-camera) │  │ (CUDA Acceleration)  │   │
│  └──────────────┘  └────────────────┘  └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. Enhanced Camera System (`src/enhanced_camera_system.py`)

**Purpose**: Core orchestration engine that manages video capture, AI processing, and event handling.

**Key Responsibilities:**
- Video frame capture from RTSP streams
- Multi-threaded processing pipeline
- AI/ML model coordination
- Event detection and recording
- Real-time display frame generation

**Thread Architecture:**
```
Main Thread
  ├─ Video Capture Thread (continuous frame grabbing)
  ├─ Processing Thread (AI/ML inference)
  ├─ Recording Thread (video file writing)
  └─ Analytics Thread (pattern analysis)
```

**Key Methods:**
- `start()`: Initialize camera and start all threads
- `stop()`: Graceful shutdown
- `process_frame()`: Main AI/ML pipeline execution
- `handle_detection()`: Event processing
- `get_display_frame()`: Generate annotated frame for UI

### 2. Camera Discovery System (`src/camera_discovery.py`)

**Purpose**: Multi-protocol camera and NVR discovery system.

**Discovery Methods:**

**a) ONVIF WS-Discovery:**
```python
# Uses SOAP-based discovery protocol
# Broadcasts UDP multicast to 239.255.255.250:3702
# Discovers ONVIF-compliant cameras
```

**b) Network Port Scanning:**
```python
# Scans common camera ports: 554, 80, 8000, 8080, 8554, 9000
# Uses ThreadPoolExecutor for concurrent scanning
# Maximum 50 concurrent connections
```

**c) NVR-Specific APIs:**

**Reolink NVR:**
```python
Endpoint: /api.cgi?cmd=GetChannelStatus
Method: GET with HTTP Basic Auth
Response: JSON with channel list, online status, names
RTSP URL Format: rtsp://{ip}:554/h264Preview_{ch:02d}_main
```

**Hikvision NVR:**
```python
Endpoint: /ISAPI/System/Video/inputs/channels
Method: GET with HTTP Digest Auth
Response: XML with channel configuration
RTSP URL Format: rtsp://{ip}:554/Streaming/Channels/{ch}01
```

**Dahua NVR:**
```python
Endpoint: /cgi-bin/magicBox.cgi?action=getProductDefinition
Method: GET with HTTP Basic Auth
Response: Text with VideoInChannel count
RTSP URL Format: rtsp://{ip}:554/cam/realmonitor?channel={ch}&subtype=0
```

**Key Features:**
- Automatic NVR type detection
- Concurrent network scanning
- Camera capability detection
- RTSP stream validation
- Manufacturer-specific URL generation

### 3. Camera Manager (`src/camera_manager.py`)

**Purpose**: Persistent camera configuration management.

**Data Structure:**
```json
{
  "cameras": [
    {
      "id": "cam_0_192_168_1_110",
      "ip": "192.168.1.110",
      "name": "Front Door Camera",
      "protocol": "reolink_nvr",
      "nvr_ip": "192.168.1.100",
      "channel": 1,
      "enabled": true,
      "settings": {
        "rotation": 90,
        "flip_horizontal": false,
        "flip_vertical": false,
        "resolution": "1080p",
        "fps": 30,
        "quality": "high"
      }
    }
  ],
  "homepage_cameras": ["cam_0_192_168_1_110"],
  "active_camera_id": "cam_0_192_168_1_110"
}
```

**Operations:**
- CRUD for camera configurations
- Homepage camera selection
- Settings persistence (`data/camera_settings.json`)
- Camera connection testing
- Settings import/export

### 4. Entity Labeling System (`src/entity_labeling.py`)

**Purpose**: Label and track frequently detected faces and vehicles.

**Face Labeling:**
```python
# Query unlabeled faces with min appearances threshold
SELECT person_name, COUNT(*) as appearances,
       MAX(timestamp) as last_seen
FROM person_appearances
WHERE person_name LIKE 'Unknown%'
  AND timestamp >= NOW() - INTERVAL '30 days'
GROUP BY person_name
HAVING COUNT(*) >= 3
ORDER BY appearances DESC
```

**Vehicle Labeling:**
```python
# Track vehicles by license plate
# Store labels in metadata JSON field
{
  "label": "My Car",
  "notes": "Honda Civic - Family vehicle",
  "labeled_at": "2025-11-10T12:00:00"
}
```

**Features:**
- Auto-suggest unlabeled entities
- Historical appearance tracking
- Label removal/editing
- Retroactive labeling (updates all historical records)

### 5. Home Assistant Settings Manager (`src/ha_settings_manager.py`)

**Purpose**: Configure MQTT integration with Home Assistant.

**Configuration Structure:**
```json
{
  "enabled": true,
  "mqtt": {
    "broker": "192.168.1.100",
    "port": 1883,
    "username": "mqtt_user",
    "password": "mqtt_pass",
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
  }
}
```

**MQTT Auto-Discovery:**
```python
# Publishes discovery messages to Home Assistant
Topic: homeassistant/binary_sensor/ai_camera/person_detected/config
Payload: {
  "name": "Person Detected",
  "state_topic": "homeassistant/ai_camera/person_detected",
  "device_class": "motion",
  "device": {
    "identifiers": ["ai_camera_system"],
    "name": "AI Camera System",
    "model": "AI Camera System",
    "manufacturer": "Custom"
  }
}
```

---

## AI/ML Pipeline

### Processing Flow

```
Camera Frame (RTSP)
      ↓
Resize & Preprocess
      ↓
┌─────────────────────────────────┐
│   YOLOv11 Object Detection      │
│   - Persons, vehicles, objects  │
│   - Bounding boxes + confidence │
│   - 80 object classes           │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│   Object-Specific Processing    │
│                                 │
│  ┌─────────────────────────┐   │
│  │ Person Detected         │   │
│  │   ↓                     │   │
│  │ Face Recognition        │   │
│  │ (DeepFace)              │   │
│  │   • Extract face ROI    │   │
│  │   • Compare embeddings  │   │
│  │   • Identify or label   │   │
│  │     as Unknown_N        │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │ Vehicle Detected        │   │
│  │   ↓                     │   │
│  │ License Plate           │   │
│  │ Recognition (EasyOCR)   │   │
│  │   • Locate plate region │   │
│  │   • OCR text extraction │   │
│  │   • Validate format     │   │
│  │   ↓                     │   │
│  │ Color Detection         │   │
│  │ (CV2 color analysis)    │   │
│  │   ↓                     │   │
│  │ Speed Estimation        │   │
│  │ (calibrated tracking)   │   │
│  │   • Track trajectory    │   │
│  │   • Calculate distance  │   │
│  │   • Compute velocity    │   │
│  └─────────────────────────┘   │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│   Behavioral Analysis           │
│   - Pattern learning            │
│   - Anomaly detection           │
│   - Activity classification     │
└─────────────────────────────────┘
      ↓
┌─────────────────────────────────┐
│   Event Processing              │
│   - Database storage            │
│   - Alert generation            │
│   - MQTT publishing             │
│   - Email notifications         │
└─────────────────────────────────┘
      ↓
Display Frame (Annotated)
```

### AI Models in Detail

**1. YOLOv11 (Ultralytics)**
```python
Model: YOLOv11n.pt (nano) or YOLOv11s.pt (small)
Input: 640x640 RGB image
Output: [batch, 84, 8400] tensor
  - 8400 predictions
  - 4 box coordinates (x, y, w, h)
  - 80 class probabilities

GPU Optimization:
  - CUDA 12.1 support
  - Mixed precision (FP16)
  - TensorRT acceleration
  - Batch processing
```

**2. DeepFace (Face Recognition)**
```python
Backend: VGG-Face, Facenet, or ArcFace
Input: Face ROI (112x112 or 160x160)
Output: 128 or 512-dim embedding vector

Process:
  1. Face detection (MTCNN/RetinaFace)
  2. Alignment (facial landmarks)
  3. Embedding extraction
  4. Cosine similarity comparison
  5. Threshold-based matching (< 0.6)
```

**3. EasyOCR (License Plate Recognition)**
```python
Language: English (en)
Input: Plate ROI (variable size)
Output: Text + confidence score

Pipeline:
  1. Text detection (CRAFT model)
  2. Recognition (CRNN model)
  3. Post-processing (format validation)
  4. Confidence filtering (> 0.5)
```

**4. Speed Estimation**
```python
Method: Pixel-to-meter calibration
Calibration: User-defined reference distance
Formula: speed = (distance_pixels / distance_meters) * fps * 3.6

Requirements:
  - Known reference distance
  - Stable camera position
  - Tracking trajectory
  - Frame rate
```

---

## Data Flow

### Real-Time Detection Flow

```
1. Frame Capture (30 FPS)
   ├─ RTSP stream read
   ├─ Frame buffer management
   └─ Timestamp association

2. Object Detection (YOLOv11)
   ├─ GPU inference (~20ms)
   ├─ Non-max suppression
   └─ Confidence filtering (> 0.5)

3. Multi-Object Tracking
   ├─ DeepSORT algorithm
   ├─ Object ID assignment
   └─ Trajectory tracking

4. Specialized AI Processing
   ├─ Face Recognition (if person detected)
   │  ├─ Face ROI extraction
   │  ├─ Embedding computation
   │  └─ Database comparison
   │
   ├─ License Plate Recognition (if vehicle detected)
   │  ├─ Plate localization
   │  ├─ OCR processing
   │  └─ Format validation
   │
   └─ Speed Estimation (if calibrated)
      ├─ Position tracking
      ├─ Distance calculation
      └─ Velocity computation

5. Event Classification
   ├─ Behavioral analysis
   ├─ Anomaly detection
   └─ Alert threshold checking

6. Data Persistence
   ├─ SQLite database insert
   ├─ JSON settings update
   └─ Video recording (if enabled)

7. External Publishing
   ├─ MQTT (Home Assistant)
   ├─ WebSocket (real-time UI)
   └─ Email (critical alerts)

8. UI Update
   ├─ Annotated frame generation
   ├─ Statistics update
   └─ WebSocket broadcast
```

### Data Persistence Flow

```
Detection Event
      ↓
┌──────────────────────────────────┐
│  Database Manager (database.py)  │
│  ┌────────────────────────────┐  │
│  │ Session Creation           │  │
│  │ ├─ SQLAlchemy Session      │  │
│  │ └─ Transaction management  │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │ Table Selection            │  │
│  │ ├─ detections              │  │
│  │ ├─ person_appearances      │  │
│  │ ├─ license_plates          │  │
│  │ ├─ vehicle_records         │  │
│  │ └─ anomalies               │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │ Record Creation            │  │
│  │ ├─ Timestamp               │  │
│  │ ├─ Object data             │  │
│  │ ├─ Metadata (JSON)         │  │
│  │ └─ Camera ID               │  │
│  └────────────────────────────┘  │
│                                  │
│  ┌────────────────────────────┐  │
│  │ Commit & Error Handling    │  │
│  │ ├─ session.commit()        │  │
│  │ ├─ Exception handling      │  │
│  │ └─ session.rollback()      │  │
│  └────────────────────────────┘  │
└──────────────────────────────────┘
      ↓
SQLite File: data/camera_system.db
```

---

## API Architecture

### REST API Endpoints (31 Total)

**Camera Discovery API:**
```
POST /api/cameras/discover
  Body: { "network_range": "192.168.1.0/24" }
  Response: { "success": true, "cameras": [...], "count": 5 }

POST /api/cameras/discover/nvr
  Body: {
    "nvr_ip": "192.168.1.100",
    "nvr_port": 80,
    "username": "admin",
    "password": "password",
    "nvr_type": "auto"  // auto, reolink, hikvision, dahua
  }
  Response: { "success": true, "cameras": [...], "nvr_type": "reolink" }

GET /api/cameras/interfaces
  Response: { "interfaces": [
    { "name": "eth0", "ip": "192.168.1.50", "cidr": "192.168.1.0/24" }
  ]}
```

**Camera Management API:**
```
GET /api/cameras
  Response: { "cameras": [...] }

POST /api/cameras
  Body: { "ip": "192.168.1.110", "name": "Front Door", ... }
  Response: { "success": true, "camera_id": "cam_0_192_168_1_110" }

PUT /api/cameras/<camera_id>
  Body: { "name": "New Name", "settings": {...} }
  Response: { "success": true }

DELETE /api/cameras/<camera_id>
  Response: { "success": true }

GET /api/cameras/homepage
  Response: { "cameras": [...], "camera_ids": [...] }

POST /api/cameras/homepage
  Body: { "camera_ids": ["cam_0_192_168_1_110", ...] }
  Response: { "success": true }

POST /api/cameras/<camera_id>/test
  Body: { "username": "admin", "password": "pass" }
  Response: {
    "success": true,
    "rtsp_tested": true,
    "http_tested": true,
    "message": "Successfully connected to Main Stream"
  }
```

**Entity Labeling API:**
```
GET /api/entities/unlabeled/faces
  Query: ?min_appearances=3&days=30
  Response: { "faces": [
    {
      "person_id": "Unknown_1",
      "appearances": 15,
      "first_seen": "2025-10-10T08:00:00",
      "last_seen": "2025-11-10T09:30:00",
      "type": "face"
    }
  ]}

GET /api/entities/unlabeled/vehicles
  Query: ?min_appearances=5&days=30
  Response: { "vehicles": [...] }

POST /api/entities/label/face
  Body: {
    "person_id": "Unknown_1",
    "name": "John Smith",
    "notes": "Regular visitor"
  }
  Response: { "success": true }

POST /api/entities/label/vehicle
  Body: {
    "identifier": "ABC123",
    "label": "My Car",
    "notes": "Honda Civic"
  }
  Response: { "success": true }

GET /api/entities/labeled
  Query: ?type=all  // all, face, vehicle
  Response: { "entities": [...] }

DELETE /api/entities/<entity_type>/<identifier>
  Response: { "success": true }

GET /api/entities/<entity_type>/<identifier>/history
  Query: ?days=30
  Response: { "history": [...] }
```

**Home Assistant API:**
```
GET /api/ha/settings
  Response: { "enabled": true, "mqtt": {...}, "publish": {...}, ... }

POST /api/ha/settings
  Body: { "mqtt": { "broker": "192.168.1.100", ... } }
  Response: { "success": true }

POST /api/ha/test
  Response: {
    "success": true,
    "broker_reachable": true,
    "authenticated": true,
    "message": "Successfully connected to MQTT broker"
  }

GET /api/ha/entities
  Response: { "entities": [
    {
      "type": "binary_sensor",
      "name": "Person Detected",
      "state_topic": "homeassistant/ai_camera/person_detected",
      "device_class": "motion"
    }
  ]}

GET /api/ha/export
  Response: { "config": "# YAML config for Home Assistant..." }
```

**Analytics API:**
```
GET /api/stats
GET /api/analytics/hourly
GET /api/analytics/activity
GET /api/analytics/frequent-objects
GET /api/speed/stats
GET /api/speed/violations
```

**Chatbot API:**
```
POST /api/chatbot/query
  Body: { "question": "How many people were detected today?", "conversation_id": "..." }
  Response: { "answer": "...", "conversation_id": "...", "relevant_data": [...] }

GET /api/chatbot/history
POST /api/chatbot/reset
```

---

## Database Schema

### Table: `detections`
```sql
CREATE TABLE detections (
  id INTEGER PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  object_type VARCHAR(50) NOT NULL,  -- person, car, truck, etc.
  object_id VARCHAR(100) NOT NULL,   -- Tracking ID
  confidence FLOAT NOT NULL,
  bbox JSON,                         -- [x, y, width, height]
  metadata JSON,                     -- {color, speed, additional_data}
  camera_id VARCHAR(50),
  is_anomaly BOOLEAN DEFAULT 0
);

CREATE INDEX idx_detections_timestamp ON detections(timestamp);
CREATE INDEX idx_detections_object_type ON detections(object_type);
CREATE INDEX idx_detections_object_id ON detections(object_id);
CREATE INDEX idx_detections_camera_id ON detections(camera_id);
```

### Table: `person_appearances`
```sql
CREATE TABLE person_appearances (
  id INTEGER PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  person_id VARCHAR(100) NOT NULL,
  person_name VARCHAR(100),          -- Name or "Unknown_N"
  confidence FLOAT NOT NULL,
  duration INTEGER,                  -- Seconds in frame
  location JSON,                     -- {x, y, width, height}
  camera_id VARCHAR(50),
  is_recognized BOOLEAN DEFAULT 0,   -- True if labeled/known
  is_unusual_time BOOLEAN DEFAULT 0  -- Outside normal patterns
);

CREATE INDEX idx_person_appearances_timestamp ON person_appearances(timestamp);
CREATE INDEX idx_person_appearances_person_id ON person_appearances(person_id);
CREATE INDEX idx_person_appearances_person_name ON person_appearances(person_name);
```

### Table: `license_plates`
```sql
CREATE TABLE license_plates (
  id INTEGER PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  plate_number VARCHAR(20),
  confidence FLOAT NOT NULL,
  vehicle_type VARCHAR(50),          -- car, truck, motorcycle
  vehicle_color VARCHAR(50),
  vehicle_id VARCHAR(100),
  country VARCHAR(10),
  camera_id VARCHAR(50),
  bbox JSON,
  raw_text VARCHAR(50),              -- Before cleaning
  metadata JSON                      -- {label, notes, labeled_at}
);

CREATE INDEX idx_license_plates_timestamp ON license_plates(timestamp);
CREATE INDEX idx_license_plates_plate_number ON license_plates(plate_number);
```

### Table: `vehicle_records`
```sql
CREATE TABLE vehicle_records (
  id INTEGER PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  vehicle_id VARCHAR(100),
  vehicle_type VARCHAR(50),
  color VARCHAR(50),
  speed FLOAT,                       -- km/h
  direction VARCHAR(20),             -- N, S, E, W, NE, etc.
  camera_id VARCHAR(50),
  metadata JSON
);

CREATE INDEX idx_vehicle_records_timestamp ON vehicle_records(timestamp);
CREATE INDEX idx_vehicle_records_vehicle_id ON vehicle_records(vehicle_id);
CREATE INDEX idx_vehicle_records_color ON vehicle_records(color);
```

### Table: `anomalies`
```sql
CREATE TABLE anomalies (
  id INTEGER PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  anomaly_type VARCHAR(50),          -- loitering, intrusion, etc.
  severity FLOAT,                    -- 0.0 to 1.0
  description TEXT,
  related_objects JSON,              -- Object IDs involved
  camera_id VARCHAR(50),
  resolved BOOLEAN DEFAULT 0
);

CREATE INDEX idx_anomalies_timestamp ON anomalies(timestamp);
CREATE INDEX idx_anomalies_anomaly_type ON anomalies(anomaly_type);
```

### Table: `activity_log`
```sql
CREATE TABLE activity_log (
  id INTEGER PRIMARY KEY,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  activity_type VARCHAR(50),         -- person_detected, vehicle_passed, etc.
  count INTEGER DEFAULT 1,
  hour INTEGER,                      -- 0-23
  day_of_week INTEGER,               -- 0-6 (Monday-Sunday)
  metadata JSON
);

CREATE INDEX idx_activity_log_timestamp ON activity_log(timestamp);
CREATE INDEX idx_activity_log_activity_type ON activity_log(activity_type);
CREATE INDEX idx_activity_log_hour ON activity_log(hour);
CREATE INDEX idx_activity_log_day_of_week ON activity_log(day_of_week);
```

---

## Configuration System

### Primary Configuration: `config.yaml`

```yaml
# Camera Configuration
camera:
  source: "rtsp://admin:password@192.168.1.110:554/h264Preview_01_main"
  resolution:
    width: 1920
    height: 1080
  fps: 30

# Detection Settings
detection:
  enable_object_detection: true
  enable_motion_detection: true
  confidence_threshold: 0.5
  yolo_model: "yolov11n.pt"  # nano, small, medium, large, xlarge

# AI Features
ai_features:
  face_recognition:
    enabled: true
    model: "VGG-Face"
    confidence_threshold: 0.6
  license_plate_recognition:
    enabled: true
    languages: ["en"]
    min_confidence: 0.5
  speed_estimation:
    enabled: true
    calibrated: true
    speed_limit: 50  # km/h
  behavioral_analysis:
    enabled: true
    learning_period_days: 30
  anomaly_detection:
    enabled: true
    sensitivity: 0.7

# Recording
recording:
  enabled: false
  path: "recordings"
  format: "mp4"
  codec: "h264"
  quality: 23  # CRF value (lower = better quality)
  segment_duration: 600  # seconds (10 minutes)
  retention_days: 30

# Database
database:
  url: "sqlite:///data/camera_system.db"
  backup_enabled: true
  backup_interval_hours: 24

# Web Interface
web:
  host: "0.0.0.0"
  port: 5000
  enable_cors: true

# Email Notifications
email:
  enabled: false
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  username: "your_email@gmail.com"
  password: "your_app_password"
  from_address: "your_email@gmail.com"
  to_addresses:
    - "recipient@example.com"
  alerts:
    person_detected: true
    vehicle_speeding: true
    anomaly_detected: true
    unknown_face: false

# Home Assistant
home_assistant:
  enabled: false
  mqtt_broker: "192.168.1.100"
  mqtt_port: 1883
  mqtt_username: ""
  mqtt_password: ""

# Performance
performance:
  use_gpu: true
  gpu_device_id: 0
  max_threads: 4
  frame_skip: 0  # Skip every N frames (0 = no skip)
```

### Persistent Settings Files

**1. `data/camera_settings.json`**
```json
{
  "cameras": [],
  "homepage_cameras": [],
  "active_camera_id": null,
  "last_updated": "2025-11-10T12:00:00"
}
```

**2. `data/ha_settings.json`**
```json
{
  "enabled": false,
  "mqtt": {...},
  "publish": {...},
  "topics": {...},
  "last_updated": "2025-11-10T12:00:00"
}
```

**3. `data/speed_calibration.json`**
```json
{
  "calibrated": false,
  "points": [],
  "pixel_distance": 0,
  "real_distance_meters": 0,
  "pixels_per_meter": 0
}
```

---

## Integration Points

### 1. Home Assistant (MQTT)

**Auto-Discovery Protocol:**
```python
# Device Configuration
Topic: homeassistant/<component>/<node_id>/<object_id>/config
Payload: {
  "name": "Person Detected",
  "state_topic": "homeassistant/ai_camera/person_detected",
  "device_class": "motion",
  "unique_id": "ai_camera_person_sensor",
  "device": {
    "identifiers": ["ai_camera_system"],
    "name": "AI Camera System",
    "model": "Professional AI Camera",
    "manufacturer": "Custom",
    "sw_version": "1.0.0"
  }
}

# State Publishing
Topic: homeassistant/ai_camera/person_detected
Payload: "ON" or "OFF"

# Attributes Publishing
Topic: homeassistant/ai_camera/person_detected/attributes
Payload: {
  "person_name": "John Smith",
  "confidence": 0.95,
  "timestamp": "2025-11-10T12:00:00",
  "camera_id": "cam_0_192_168_1_110"
}
```

**Published Entities:**
- `binary_sensor.ai_camera_person_detected`
- `binary_sensor.ai_camera_vehicle_detected`
- `binary_sensor.ai_camera_motion`
- `sensor.ai_camera_vehicle_speed`
- `sensor.ai_camera_activity_level`
- `sensor.ai_camera_license_plate`
- `binary_sensor.ai_camera_anomaly`

### 2. Email Notifications

**SMTP Configuration:**
```python
# Uses smtplib with TLS
Server: smtp.gmail.com
Port: 587
Authentication: Username/Password or App Password
```

**Alert Types:**
- Person detected (with face snapshot)
- Vehicle speeding (with plate + speed)
- Anomaly detected (with description)
- Unknown face (with image)
- System errors

**Email Template:**
```
Subject: [AI Camera Alert] Person Detected

Timestamp: 2025-11-10 12:00:00
Camera: Front Door Camera
Event: Person Detected
Person: John Smith
Confidence: 95%

[Snapshot Image Embedded]

Details:
- Location: Near entrance
- Duration: 15 seconds
- Activity: Normal

View full details: http://192.168.1.50:5000/analytics
```

### 3. External APIs (Future)

- Telegram Bot notifications
- Discord webhooks
- Pushover/Pushbullet
- Cloud storage (AWS S3, Google Drive)
- Third-party NVR systems

---

## Deployment Architecture

### Hardware Requirements

**Minimum:**
- CPU: Intel Core i5 (8th gen) or AMD Ryzen 5
- RAM: 8 GB
- GPU: NVIDIA GTX 1060 (6GB VRAM)
- Storage: 50 GB SSD (system) + 500 GB HDD (recordings)
- Network: Gigabit Ethernet

**Recommended (Production):**
- CPU: Intel Core i7 (12th gen) or AMD Ryzen 7
- RAM: 16 GB DDR4
- GPU: NVIDIA RTX 4070 Ti (12GB VRAM)
- Storage: 256 GB NVMe SSD (system) + 2 TB HDD (recordings)
- Network: Gigabit Ethernet

### Software Environment

**Operating System:**
- Ubuntu 22.04 LTS (primary)
- Ubuntu 24.04 LTS (supported)
- Debian 12
- Windows 10/11 (with WSL2)

**Python Environment:**
```bash
Python 3.12+
CUDA 12.1+
cuDNN 8.9+
```

**NVIDIA Driver:**
```bash
# Check current driver
nvidia-smi

# Recommended: Driver 535+ for CUDA 12.1
sudo apt install nvidia-driver-535
```

### Installation Process

**1. System Dependencies:**
```bash
sudo apt update
sudo apt install -y \
  python3.12 python3.12-venv python3-pip \
  build-essential cmake git \
  libopencv-dev python3-opencv \
  ffmpeg libavcodec-dev libavformat-dev libavutil-dev \
  libsqlite3-dev
```

**2. Python Virtual Environment:**
```bash
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**3. CUDA Setup (GPU):**
```bash
# Verify CUDA installation
nvcc --version

# Test PyTorch CUDA
python3 -c "import torch; print(torch.cuda.is_available())"
```

**4. Database Initialization:**
```bash
# Auto-created on first run
mkdir -p data
python3 -c "from src.database import DatabaseManager; DatabaseManager()"
```

**5. Configuration:**
```bash
cp config.yaml.example config.yaml
nano config.yaml  # Edit settings
```

**6. Run System:**
```bash
# Simple mode
python3 main.py

# Enhanced mode (all AI features)
python3 main_enhanced.py

# Headless mode (no display window)
python3 main.py --headless

# With recording
python3 main.py --record

# Custom config
python3 main.py --config my_config.yaml
```

### Docker Deployment (Optional)

**Dockerfile:**
```dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.12 python3-pip \
    libopencv-dev ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python3", "main_enhanced.py", "--headless"]
```

**Docker Compose:**
```yaml
version: '3.8'

services:
  ai_camera:
    build: .
    container_name: ai_camera_system
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=0
      - NVIDIA_DRIVER_CAPABILITIES=compute,utility
    ports:
      - "5000:5000"
    volumes:
      - ./data:/app/data
      - ./recordings:/app/recordings
      - ./config.yaml:/app/config.yaml
    restart: unless-stopped
```

### Systemd Service (Production)

**File:** `/etc/systemd/system/ai-camera.service`
```ini
[Unit]
Description=AI Camera System
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/mnt/disk_980g/Projuice/Projuice
Environment="PATH=/mnt/disk_980g/Projuice/Projuice/venv/bin"
ExecStart=/mnt/disk_980g/Projuice/Projuice/venv/bin/python3 main_enhanced.py --headless
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and Start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-camera
sudo systemctl start ai-camera
sudo systemctl status ai-camera
```

---

## Performance Optimization

### GPU Optimization

**CUDA Settings:**
```python
# In code
torch.backends.cudnn.benchmark = True
torch.backends.cudnn.deterministic = False

# Set GPU device
os.environ['CUDA_VISIBLE_DEVICES'] = '0'
```

**Memory Management:**
```python
# Clear CUDA cache periodically
torch.cuda.empty_cache()

# Use mixed precision
from torch.cuda.amp import autocast
with autocast():
    outputs = model(inputs)
```

### Processing Optimization

**Frame Skip Strategy:**
```python
# Skip frames to reduce processing load
# Process every 2nd frame (15 FPS effective)
if frame_count % 2 == 0:
    process_frame(frame)
```

**Async Processing:**
```python
# Use ThreadPoolExecutor for I/O operations
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)
future = executor.submit(save_to_database, detection)
```

**Batch Processing:**
```python
# Process multiple frames in one inference
batch_frames = [frame1, frame2, frame3, frame4]
results = model(batch_frames)  # 4x faster than individual
```

---

## Troubleshooting

### Common Issues

**1. CUDA Out of Memory:**
```python
Solution:
- Reduce batch size
- Use smaller YOLO model (nano instead of large)
- Lower camera resolution
- Enable frame skipping
```

**2. High CPU Usage:**
```python
Solution:
- Verify GPU is being used (nvidia-smi)
- Reduce FPS
- Disable unnecessary AI features
- Optimize database queries
```

**3. Camera Connection Failures:**
```python
Solution:
- Verify RTSP URL format
- Check network connectivity (ping camera IP)
- Verify credentials
- Test with VLC: vlc rtsp://...
- Check firewall rules
```

**4. Face Recognition Low Accuracy:**
```python
Solution:
- Ensure good lighting
- Increase confidence threshold
- Add more training images
- Use higher resolution camera
- Check face alignment
```

---

## Security Considerations

**1. RTSP Credentials:**
- Store passwords in environment variables
- Use `.env` file (excluded from git)
- Consider using VPN for camera access

**2. Web Interface:**
- Enable HTTPS (reverse proxy with nginx)
- Implement authentication
- Use strong SECRET_KEY
- Rate limiting on API endpoints

**3. Database:**
- Regular backups
- Encrypted storage for sensitive data
- Access control

**4. Home Assistant:**
- Use MQTT over TLS
- Strong MQTT passwords
- Isolate on separate VLAN

---

## Future Enhancements

**Planned Features:**
1. Multi-camera synchronized tracking
2. 3D object tracking
3. Advanced behavioral predictions
4. Cloud backup integration
5. Mobile app (iOS/Android)
6. PTZ camera control
7. Audio detection and analysis
8. Thermal camera support
9. Crowd counting and heatmaps
10. Integration with access control systems

---

## Conclusion

This architecture document provides a comprehensive understanding of the Home AI ML Camera System. The system is designed to be modular, scalable, and maintainable while delivering professional-grade AI-powered surveillance capabilities.

For API usage details, see `API_DOCUMENTATION.md`.
For installation instructions, see `README.md`.
For contribution guidelines, see `CONTRIBUTING.md`.

---

**Document Version:** 1.0.0
**Last Updated:** 2025-11-10
**Maintained By:** Project Development Team
