# 🏠 Home AI and ML Camera System

A powerful, AI-powered home surveillance system with real-time object detection, motion tracking, and intelligent alerts using state-of-the-art machine learning models.

## ✨ Features

### 🎯 Core Capabilities
- **Real-time Object Detection** - Powered by YOLOv8 for accurate and fast object recognition
- **Motion Detection** - Advanced background subtraction for motion tracking
- **Face Detection** - Optional face detection using Haar Cascades
- **Video Recording** - Automatic recording with event triggers
- **Snapshot Management** - Capture and save important moments
- **Event Logging** - Comprehensive event tracking and analysis

### 🌐 Web Interface
- **Live Video Streaming** - Real-time video feed in your browser
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
