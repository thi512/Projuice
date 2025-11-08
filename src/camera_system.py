"""
Main camera system that integrates all components
"""
import cv2
import logging
import time
from datetime import datetime
from threading import Thread
import numpy as np

from .camera import Camera
from .detector import ObjectDetector, MotionDetector, FaceDetector
from .recorder import VideoRecorder, EventLogger, SnapshotManager
from .config import Config

logger = logging.getLogger(__name__)


class CameraSystem:
    """Main camera system integrating all components"""

    def __init__(self, config_file="config.yaml"):
        """
        Initialize camera system

        Args:
            config_file: Path to configuration file
        """
        self.config = Config(config_file)
        self.camera = None
        self.object_detector = None
        self.motion_detector = None
        self.face_detector = None
        self.recorder = None
        self.event_logger = None
        self.snapshot_manager = None

        self.is_running = False
        self.is_recording = False
        self.process_thread = None
        self.display_frame = None
        self.start_time = None

        # Statistics
        self.stats = {
            'frames_processed': 0,
            'detections': {},
            'motion_events': 0,
            'recordings': 0,
            'snapshots': 0
        }

        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize all system components"""
        # Camera
        cam_config = self.config.get_camera_config()
        self.camera = Camera(**cam_config)

        # Detectors
        det_config = self.config.get_detector_config()

        if det_config['enable_object_detection']:
            try:
                self.object_detector = ObjectDetector(
                    model_type=det_config['model_type'],
                    confidence_threshold=det_config['confidence_threshold'],
                    device=det_config['device']
                )
            except Exception as e:
                logger.error(f"Failed to initialize object detector: {e}")

        if det_config['enable_motion_detection']:
            self.motion_detector = MotionDetector(
                threshold=det_config['motion_threshold'],
                min_area=det_config['motion_min_area']
            )

        if det_config['enable_face_detection']:
            self.face_detector = FaceDetector()

        # Recorder
        rec_config = self.config.get_recorder_config()
        self.recorder = VideoRecorder(
            output_dir=rec_config['output_dir'],
            codec=rec_config['codec'],
            fps=cam_config['fps']
        )

        self.event_logger = EventLogger(rec_config['output_dir'])
        self.snapshot_manager = SnapshotManager()

        logger.info("Camera system components initialized")

    def start(self):
        """Start the camera system"""
        if self.is_running:
            logger.warning("Camera system already running")
            return False

        logger.info("Starting camera system")

        # Start camera
        if not self.camera.start():
            logger.error("Failed to start camera")
            return False

        self.is_running = True
        self.start_time = datetime.now()

        # Start processing thread
        self.process_thread = Thread(target=self._process_loop, daemon=True)
        self.process_thread.start()

        logger.info("Camera system started successfully")
        return True

    def _process_loop(self):
        """Main processing loop"""
        frame_count = 0
        last_detection_time = 0
        alert_cooldown = self.config.get('alerts.alert_cooldown', 60)
        process_every_n = self.config.get('performance.process_every_n_frames', 1)

        while self.is_running:
            # Read frame from camera
            ret, frame = self.camera.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1
            self.stats['frames_processed'] = frame_count

            # Skip frames if configured
            if frame_count % process_every_n != 0:
                self.display_frame = frame.copy()
                continue

            display_frame = frame.copy()
            current_time = time.time()

            # Motion detection
            if self.motion_detector:
                motion_detected, motion_mask, contours = self.motion_detector.detect(frame)

                if motion_detected:
                    self.stats['motion_events'] += 1
                    display_frame = self.motion_detector.draw_motion(display_frame, contours)

                    # Log motion event
                    if current_time - last_detection_time > alert_cooldown:
                        self.event_logger.log_event('motion', {
                            'num_contours': len(contours),
                            'frame_number': frame_count
                        })
                        last_detection_time = current_time

            # Object detection
            if self.object_detector:
                target_classes = self.config.get('detection.target_classes')
                detections = self.object_detector.detect(frame, target_classes)

                if detections:
                    display_frame = self.object_detector.draw_detections(display_frame, detections)

                    # Update statistics
                    for det in detections:
                        class_name = det['class']
                        self.stats['detections'][class_name] = \
                            self.stats['detections'].get(class_name, 0) + 1

                    # Log detection event
                    if current_time - last_detection_time > alert_cooldown:
                        self.event_logger.log_event('object_detection', {
                            'detections': detections,
                            'frame_number': frame_count
                        })

                        # Auto-snapshot on person detection
                        if any(d['class'] == 'person' for d in detections):
                            self.snapshot_manager.save_snapshot(
                                display_frame,
                                prefix='person_detected',
                                metadata={'detections': detections}
                            )
                            self.stats['snapshots'] += 1

                        last_detection_time = current_time

            # Face detection
            if self.face_detector:
                faces = self.face_detector.detect(frame)
                if len(faces) > 0:
                    display_frame = self.face_detector.draw_faces(display_frame, faces)

            # Add info overlay
            display_frame = self._add_info_overlay(display_frame, frame_count)

            # Update display frame
            self.display_frame = display_frame

            # Record frame if recording
            if self.is_recording and self.recorder:
                self.recorder.write_frame(display_frame)

    def _add_info_overlay(self, frame, frame_count):
        """Add information overlay to frame"""
        height, width = frame.shape[:2]

        # Create semi-transparent overlay
        overlay = frame.copy()

        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(overlay, timestamp, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Add recording indicator
        if self.is_recording:
            cv2.circle(overlay, (width - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(overlay, "REC", (width - 80, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # Add frame count
        cv2.putText(overlay, f"Frame: {frame_count}", (10, height - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return overlay

    def start_recording(self):
        """Start video recording"""
        if self.is_recording:
            logger.warning("Already recording")
            return False

        if self.recorder and self.display_frame is not None:
            height, width = self.display_frame.shape[:2]
            filepath = self.recorder.start_recording(width, height)

            if filepath:
                self.is_recording = True
                self.stats['recordings'] += 1
                logger.info(f"Started recording to {filepath}")
                return True

        return False

    def stop_recording(self):
        """Stop video recording"""
        if not self.is_recording:
            return None

        if self.recorder:
            filepath = self.recorder.stop_recording()
            self.is_recording = False
            logger.info(f"Stopped recording: {filepath}")
            return filepath

        return None

    def take_snapshot(self):
        """Take a snapshot of current frame"""
        if self.display_frame is not None:
            filepath = self.snapshot_manager.save_snapshot(self.display_frame)
            self.stats['snapshots'] += 1
            return filepath
        return None

    def get_display_frame(self):
        """Get current display frame for streaming"""
        return self.display_frame

    def get_stats(self):
        """Get system statistics"""
        return self.stats.copy()

    def stop(self):
        """Stop the camera system"""
        logger.info("Stopping camera system")
        self.is_running = False

        # Stop recording if active
        if self.is_recording:
            self.stop_recording()

        # Wait for processing thread
        if self.process_thread:
            self.process_thread.join(timeout=5.0)

        # Stop camera
        if self.camera:
            self.camera.stop()

        # Save events
        if self.event_logger:
            self.event_logger.save_events()

        logger.info("Camera system stopped")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
