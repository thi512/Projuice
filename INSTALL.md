# Installation Guide

This guide provides detailed installation instructions for the Home AI and ML Camera System.

## Table of Contents
- [System Requirements](#system-requirements)
- [Installation on Linux](#installation-on-linux)
- [Installation on macOS](#installation-on-macos)
- [Installation on Windows](#installation-on-windows)
- [GPU Support](#gpu-support)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Minimum Requirements
- **OS**: Linux, macOS, or Windows 10+
- **Python**: 3.8 or higher
- **RAM**: 4GB (8GB recommended)
- **Disk Space**: 2GB free space
- **Camera**: USB webcam or IP camera

### Recommended Requirements
- **RAM**: 8GB or more
- **GPU**: NVIDIA GPU with CUDA support (for faster processing)
- **Camera**: HD webcam (720p or higher)

## Installation on Linux

### Ubuntu/Debian

1. **Update system packages**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. **Install system dependencies**
   ```bash
   sudo apt install -y python3 python3-pip python3-venv
   sudo apt install -y libopencv-dev python3-opencv
   sudo apt install -y libgl1-mesa-glx libglib2.0-0
   ```

3. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Projuice
   ```

4. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

5. **Install Python dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. **Configure camera permissions** (if needed)
   ```bash
   sudo usermod -a -G video $USER
   # Log out and log back in for changes to take effect
   ```

7. **Run the application**
   ```bash
   python main.py
   ```

### CentOS/RHEL/Fedora

1. **Install dependencies**
   ```bash
   sudo dnf install -y python3 python3-pip python3-virtualenv
   sudo dnf install -y opencv opencv-python
   ```

2. **Follow steps 3-7 from Ubuntu installation**

## Installation on macOS

1. **Install Homebrew** (if not already installed)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python and dependencies**
   ```bash
   brew install python@3.11
   brew install opencv
   ```

3. **Clone and setup**
   ```bash
   git clone <repository-url>
   cd Projuice
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Grant camera permissions**
   - Go to System Preferences → Security & Privacy → Camera
   - Allow Terminal (or your terminal app) to access the camera

5. **Run the application**
   ```bash
   python main.py
   ```

### Apple Silicon (M1/M2) Specific

For Apple Silicon Macs, you can use MPS (Metal Performance Shaders) acceleration:

1. Install TensorFlow for Apple Silicon:
   ```bash
   pip install tensorflow-macos
   pip install tensorflow-metal
   ```

2. Update `config.yaml`:
   ```yaml
   ml_model:
     device: "mps"
   ```

## Installation on Windows

### Using Windows 10/11

1. **Install Python**
   - Download Python 3.11 from [python.org](https://www.python.org/downloads/)
   - Run installer and check "Add Python to PATH"
   - Verify installation: `python --version`

2. **Install Visual C++ Redistributable**
   - Download from [Microsoft](https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist)
   - Required for OpenCV

3. **Clone the repository**
   ```powershell
   git clone <repository-url>
   cd Projuice
   ```

4. **Create virtual environment**
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```

5. **Install dependencies**
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. **Run the application**
   ```powershell
   python main.py
   ```

## GPU Support

### NVIDIA GPU (CUDA)

For much faster inference with NVIDIA GPUs:

1. **Install NVIDIA drivers**
   - Download latest drivers from [NVIDIA website](https://www.nvidia.com/download/index.aspx)

2. **Install CUDA Toolkit**
   - Download CUDA 11.8 or 12.x from [NVIDIA CUDA](https://developer.nvidia.com/cuda-downloads)
   - Follow installation instructions for your OS

3. **Install cuDNN**
   - Download cuDNN from [NVIDIA cuDNN](https://developer.nvidia.com/cudnn)
   - Extract and copy files to CUDA directory

4. **Install PyTorch with CUDA**
   ```bash
   pip uninstall torch torchvision
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
   ```

5. **Update config.yaml**
   ```yaml
   ml_model:
     device: "cuda"
   ```

6. **Verify CUDA**
   ```python
   import torch
   print(torch.cuda.is_available())  # Should print True
   ```

## Docker Installation (Alternative)

Run the system in a Docker container:

```bash
# Build image
docker build -t home-ai-camera .

# Run container
docker run -it --rm \
  --device=/dev/video0 \
  -p 5000:5000 \
  -v $(pwd)/recordings:/app/recordings \
  home-ai-camera
```

## Troubleshooting

### "ImportError: No module named cv2"
```bash
pip install opencv-python opencv-contrib-python
```

### "Camera not accessible"
- **Linux**: Add user to video group
  ```bash
  sudo usermod -a -G video $USER
  ```
- **macOS**: Grant camera permissions in System Preferences
- **Windows**: Check camera is not being used by another application

### "YOLO model download fails"
- Check internet connectivity
- Manually download model from [Ultralytics](https://github.com/ultralytics/assets/releases)
- Place in `~/.cache/torch/hub/ultralytics/`

### "Port 5000 already in use"
Edit `config.yaml`:
```yaml
web_interface:
  port: 8080  # Use different port
```

### Low FPS or high CPU usage
1. Use smaller model: `yolov8n` instead of `yolov8l`
2. Reduce resolution in config
3. Increase `process_every_n_frames`
4. Enable GPU acceleration

### "ModuleNotFoundError: No module named 'ultralytics'"
```bash
pip install ultralytics
```

## Verifying Installation

Run the verification script:

```python
# verify_install.py
import cv2
import sys

print(f"Python version: {sys.version}")
print(f"OpenCV version: {cv2.__version__}")

try:
    from ultralytics import YOLO
    print("✓ Ultralytics YOLO installed")
except ImportError:
    print("✗ Ultralytics not installed")

try:
    import flask
    print("✓ Flask installed")
except ImportError:
    print("✗ Flask not installed")

# Test camera
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✓ Camera accessible")
    cap.release()
else:
    print("✗ Camera not accessible")
```

## Getting Help

If you encounter issues not covered here:
1. Check the main [README.md](README.md)
2. Search existing GitHub issues
3. Create a new issue with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce

---

**Happy monitoring! 🎥**
