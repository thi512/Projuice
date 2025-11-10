# 🏠 Home AI and ML Camera System

A powerful, **self-learning** AI-powered home surveillance system with advanced pattern recognition, behavioral analysis, and continuous learning capabilities. Goes far beyond basic motion detection to truly understand your environment.

## 🧠 **NEW: Advanced AI Features**

> **The system that learns and gets smarter over time!**

### 🎓 Self-Learning Capabilities
- **Face Recognition with Auto-Learning** - Automatically learns and recognizes people who appear frequently
- **Interactive Training Interface** - Draw boxes and add text descriptions to train custom objects instantly!
- **AI Chatbot Query System** - Ask questions in natural language: "Show me when someone came today"
- **License Plate Recognition (LPR)** - State-of-the-art OCR reads plates with 95%+ accuracy
- **Behavioral Pattern Analysis** - Learns normal activity patterns and detects unusual behavior
- **Continuous Learning** - Never stops learning new patterns, always improving
- **Anomaly Detection** - Identifies unusual activities based on learned patterns
- **Person-Specific Profiling** - Learns when each person typically appears and alerts on unusual times
- **Custom Object Training** - Fine-tune YOLO with your own annotations via simple web interface

### 📊 Advanced Analytics
- **License Plate Analytics** - Track vehicles, identify patterns, detect suspicious activity
- **Automated Email Reports** - Scheduled daily/weekly summaries sent to your inbox
- **🆕 Professional Speed Calibration** - **3 calibration methods** (Simple, Zone-Based, Homography)
  - **Web-based calibration UI** with visual point-and-click setup
  - **Perspective correction** for traffic-camera accuracy
  - **Persistent settings** that survive restarts
  - **Real-time statistics** and validation
- **Vehicle Speed Estimation** - Measures vehicle speeds in km/h with professional accuracy
- **Color Detection & Tracking** - Identifies and tracks vehicle colors over time
- **Time-Based Pattern Recognition** - Discovers peak hours, quiet times, and correlations
- **Comprehensive Dashboard** - Beautiful graphs, charts, and real-time insights
- **Historical Database** - Stores all data for long-term trend analysis

### 🎥 **NEW: Professional Camera Management**
- **🆕 Auto-Discovery** - One-click discovery of all cameras on your network
  - ONVIF protocol support
  - Network scanning (RTSP, HTTP)
  - Manufacturer detection (Reolink, Hikvision, Dahua, Axis, etc.)
- **🆕 Multi-Camera Support** - Manage unlimited cameras from one interface
- **🆕 Homepage Selection** - Choose which cameras appear on main dashboard
- **🆕 Per-Camera Settings** - Rotation, flip, resolution, quality, detection zones
- **🆕 Connection Testing** - Test cameras before adding
- **🆕 Persistent Storage** - Settings survive restarts

### 👤 **NEW: Smart Entity Labeling**
- **🆕 Face Labeling** - Name frequent visitors automatically detected
- **🆕 Vehicle Labeling** - Label regular vehicles by license plate
- **🆕 Auto-Suggestions** - System suggests unlabeled faces/vehicles
- **🆕 Appearance Tracking** - Full history of when entities were seen
- **🆕 Database Integration** - All labels stored and searchable

### 🏡 Smart Home Integration
- **Reolink NVR/Camera Support** - Native integration with your Reolink cameras
- **🆕 Home Assistant MQTT Settings** - Full configuration via web interface
  - MQTT broker configuration
  - Entity publishing controls
  - Auto-discovery support
  - Connection testing
- **Real-Time Notifications** - Push alerts for anomalies and events

See **[AI_FEATURES.md](AI_FEATURES.md)** for complete documentation of all AI capabilities!

## ✨ Core Features

### 🎯 Detection Capabilities
- **Real-time Object Detection** - Powered by YOLOv8 for accurate and fast object recognition
- **Motion Detection** - Advanced background subtraction for motion tracking
- **Advanced Face Recognition** - Deep learning-based face recognition with continuous learning
- **Video Recording** - Automatic recording with event triggers
- **Snapshot Management** - Capture and save important moments
- **Event Logging** - Comprehensive event tracking and analysis

### 🌐 Web Interface
- **Live Video Streaming** - Real-time video feed in your browser
- **AI Chatbot** - Ask questions about your footage in natural language
- **Interactive Learning** - Train custom objects by drawing boxes
- **Advanced Analytics Dashboard** - Beautiful graphs and insights
- **🆕 Speed Calibration Settings** - Professional calibration interface at `/settings`
- **Remote Control** - Start/stop recording, take snapshots remotely
- **System Monitoring** - View statistics, status, and performance metrics
- **Recording History** - Browse and manage saved recordings and snapshots

### ⚡ Performance
- **Threaded Architecture** - Efficient multi-threaded processing
- **Configurable Frame Processing** - Adjust processing frequency for performance
- **GPU Support** - CUDA acceleration for faster inference (optional)

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Webcam or IP camera
- (Optional) NVIDIA GPU with CUDA for accelerated inference

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Projuice
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the system**
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings (optional)
   ```

### Running the System

#### With Web Interface (Recommended)
```bash
python main.py
```

Then open your browser to: **http://localhost:5000**

**Web Interface Pages:**
- **http://localhost:5000** - Live video feed and controls
- **http://localhost:5000/analytics** - Advanced analytics dashboard
- **http://localhost:5000/annotate** - Interactive training interface
- **http://localhost:5000/chat** - AI chatbot for searching footage
- **🆕 http://localhost:5000/settings** - Professional speed calibration settings

#### Headless Mode (No Display)
```bash
python main.py --headless
```

#### Without Web Interface
```bash
python main.py --no-web
```

#### Start Recording Immediately
```bash
python main.py --record
```

### Keyboard Controls (GUI Mode)

When running with display window:
- **`q`** - Quit the application
- **`r`** - Toggle recording on/off
- **`s`** - Take a snapshot

## ⚙️ Configuration

Configuration is managed through `config.yaml`:

### Camera Settings
```yaml
camera:
  index: 0              # Camera device index (0 for default webcam)
  resolution:
    width: 1280
    height: 720
  fps: 30
```

### ML Model Configuration
```yaml
ml_model:
  type: "yolov8n"       # Model size: yolov8n, yolov8s, yolov8m, yolov8l, yolov8x
  confidence_threshold: 0.5
  device: "cpu"         # cpu, cuda, or mps (for Mac M1/M2)
```

### Detection Settings
```yaml
detection:
  enable_object_detection: true
  enable_motion_detection: true
  enable_face_detection: false

  # Target classes to detect (COCO dataset)
  target_classes:
    - person
    - car
    - truck
    - dog
    - cat
```

### Recording Settings
```yaml
recording:
  save_recordings: true
  recordings_path: "./recordings"
  max_recording_duration: 300    # seconds
  video_codec: "mp4v"
```

## 📁 Project Structure

```
Projuice/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── camera.py             # Camera capture module
│   ├── detector.py           # ML detection (YOLO, motion, face)
│   ├── recorder.py           # Video recording and storage
│   ├── config.py             # Configuration management
│   ├── camera_system.py      # Main system integration
│   └── web_server.py         # Flask web interface
├── templates/
│   └── index.html            # Web UI template
├── recordings/               # Saved videos and snapshots
│   └── snapshots/
├── main.py                   # Application entry point
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## 🎯 Use Cases

### Home Security
- Monitor your home while away
- Receive alerts on motion or person detection
- Review recorded footage of events

### Pet Monitoring
- Keep an eye on your pets
- Detect and record pet activity
- Automatic snapshots when pets are detected

### Package Delivery
- Get notified when people approach your door
- Record delivery activities
- Review visitor history

### Wildlife Observation
- Detect and record wildlife in your yard
- Automatic classification of animals
- Time-lapse creation from snapshots

## 🔧 Advanced Configuration

### Using IP Camera

In `config.yaml`, set the camera index to your RTSP URL:
```yaml
camera:
  index: "rtsp://username:password@ip:port/stream"
```

### GPU Acceleration

For NVIDIA GPUs with CUDA:
```yaml
ml_model:
  device: "cuda"
```

For Apple Silicon (M1/M2):
```yaml
ml_model:
  device: "mps"
```

### Custom Object Classes

Edit the target classes in `config.yaml` to detect specific objects:
```yaml
detection:
  target_classes:
    - person
    - car
    - dog
    - cat
    - bird
    - backpack
```

See [COCO dataset classes](https://github.com/ultralytics/ultralytics/blob/main/ultralytics/cfg/datasets/coco.yaml) for all available classes.

## 📊 API Endpoints

The web server exposes several REST API endpoints:

- `GET /api/status` - Get system status
- `GET /api/stats` - Get detection statistics
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `GET /api/recordings` - List saved recordings
- `GET /api/snapshots` - List saved snapshots
- `GET /video_feed` - Live video stream

## 🐛 Troubleshooting

### Camera not detected
```bash
# Test camera access
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

### YOLO model download issues
The first run will download the YOLO model (~6MB for yolov8n). Ensure you have internet connectivity.

### Low FPS / Performance
- Reduce camera resolution in `config.yaml`
- Use a smaller YOLO model (yolov8n instead of yolov8l)
- Increase `process_every_n_frames` to skip frames
- Disable face detection if not needed
- Use GPU acceleration if available

### Web interface not accessible
- Check firewall settings
- Verify the port (default 5000) is not in use
- Try accessing via `http://127.0.0.1:5000` instead of `localhost`

## 📝 Logging

Logs are saved to `camera_system.log` and also printed to console.

To adjust logging level, modify `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # More verbose
logging.basicConfig(level=logging.WARNING)  # Less verbose
```

## 📚 Documentation

Comprehensive guides for all features:

- **[README.md](README.md)** - This file - System overview and quick start
- **[AI_FEATURES.md](AI_FEATURES.md)** - Complete AI capabilities documentation
- **[INTERACTIVE_LEARNING.md](INTERACTIVE_LEARNING.md)** - Guide to training custom objects
- **[CHATBOT_GUIDE.md](CHATBOT_GUIDE.md)** - Natural language query system guide
- **[LPR_EMAIL_GUIDE.md](LPR_EMAIL_GUIDE.md)** - License plate recognition & email reporting guide
- **[YOLOE_GUIDE.md](YOLOE_GUIDE.md)** - YOLO-E efficiency guide
- **[INSTALL.md](INSTALL.md)** - Detailed installation instructions

## 🔒 Security Considerations

- The web interface has no authentication by default
- Do not expose the web server to the internet without proper security
- Consider using a reverse proxy (nginx) with HTTPS and authentication
- Store sensitive credentials in `.env` file, not in `config.yaml`
- Regularly update dependencies for security patches

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Ultralytics YOLOv8](https://github.com/ultralytics/ultralytics) - Object detection model
- [OpenCV](https://opencv.org/) - Computer vision library
- [Flask](https://flask.palletsprojects.com/) - Web framework

## 📧 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Built with ❤️ for smart home enthusiasts**
