"""
Camera module for capturing video from webcam or IP camera
"""
import cv2
import logging
from threading import Thread, Lock
from queue import Queue
import time

logger = logging.getLogger(__name__)


class Camera:
    """Handle camera capture with threading for better performance"""

    def __init__(self, camera_index=0, width=1280, height=720, fps=30):
        """
        Initialize camera

        Args:
            camera_index: Camera device index or RTSP URL
            width: Frame width
            height: Frame height
            fps: Frames per second
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.frame = None
        self.frame_lock = Lock()
        self.is_running = False
        self.thread = None
        self.frame_count = 0

    def start(self):
        """Start the camera capture thread"""
        if self.is_running:
            logger.warning("Camera is already running")
            return False

        logger.info(f"Starting camera {self.camera_index}")
        self.cap = cv2.VideoCapture(self.camera_index)

        if not self.cap.isOpened():
            logger.error(f"Failed to open camera {self.camera_index}")
            return False

        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        # Verify settings
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(self.cap.get(cv2.CAP_PROP_FPS))

        logger.info(f"Camera initialized: {actual_width}x{actual_height} @ {actual_fps}fps")

        self.is_running = True
        self.thread = Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

        return True

    def _capture_loop(self):
        """Continuous capture loop running in separate thread"""
        while self.is_running:
            ret, frame = self.cap.read()

            if ret:
                with self.frame_lock:
                    self.frame = frame
                    self.frame_count += 1
            else:
                logger.warning("Failed to read frame from camera")
                time.sleep(0.1)

    def read(self):
        """
        Get the latest frame from camera

        Returns:
            tuple: (success, frame)
        """
        with self.frame_lock:
            if self.frame is None:
                return False, None
            return True, self.frame.copy()

    def get_frame_count(self):
        """Get total number of frames captured"""
        return self.frame_count

    def stop(self):
        """Stop camera capture and release resources"""
        logger.info("Stopping camera")
        self.is_running = False

        if self.thread is not None:
            self.thread.join(timeout=2.0)

        if self.cap is not None:
            self.cap.release()

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()


class CameraManager:
    """Manage multiple cameras"""

    def __init__(self):
        self.cameras = {}

    def add_camera(self, name, camera_index=0, width=1280, height=720, fps=30):
        """Add a new camera"""
        camera = Camera(camera_index, width, height, fps)
        self.cameras[name] = camera
        return camera

    def start_all(self):
        """Start all cameras"""
        for name, camera in self.cameras.items():
            logger.info(f"Starting camera: {name}")
            camera.start()

    def stop_all(self):
        """Stop all cameras"""
        for name, camera in self.cameras.items():
            logger.info(f"Stopping camera: {name}")
            camera.stop()

    def get_camera(self, name):
        """Get camera by name"""
        return self.cameras.get(name)
