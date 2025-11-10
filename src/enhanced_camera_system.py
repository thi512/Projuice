"""
Enhanced Camera System integrating all AI features:
- Face recognition with learning
- Behavioral analysis
- Pattern recognition
- Anomaly detection
- Vehicle analytics (speed, color)
- Continuous learning
- Database storage
- Home Assistant integration
- Reolink camera support
"""
import cv2
import logging
import time
from datetime import datetime
from threading import Thread
import numpy as np

from .camera import Camera
from .detector import ObjectDetector, MotionDetector
from .recorder import VideoRecorder, EventLogger, SnapshotManager
from .config import Config
from .face_recognition_ai import FaceRecognitionSystem
from .behavioral_analysis import BehavioralAnalysisEngine
from .advanced_analytics import AdvancedAnalytics
from .professional_speed_estimation import PerspectiveSpeedEstimator
from .database import DatabaseManager
from .continuous_learning import ContinuousLearningSystem
from .reolink_integration import ReolinkIntegration
from .home_assistant_mqtt import HomeAssistantMQTT
from .interactive_learning import InteractiveLearningManager

logger = logging.getLogger(__name__)


class EnhancedCameraSystem:
    """Enhanced camera system with full AI capabilities"""

    def __init__(self, config_file="config.yaml"):
        """Initialize enhanced camera system"""
        self.config = Config(config_file)
        self.camera = None
        self.object_detector = None
        self.motion_detector = None
        self.recorder = None
        self.event_logger = None
        self.snapshot_manager = None

        # Advanced AI components
        self.face_ai = None
        self.behavior = None
        self.analytics = None
        self.speed_estimator = None  # Professional speed estimation
        self.db = None
        self.learning_system = None
        self.reolink = None
        self.home_assistant = None
        self.interactive_learning = None

        self.is_running = False
        self.is_recording = False
        self.process_thread = None
        self.display_frame = None
        self.start_time = None

        # Statistics and insights
        self.stats = {
            'frames_processed': 0,
            'detections': {},
            'motion_events': 0,
            'recordings': 0,
            'snapshots': 0,
            'people_recognized': 0,
            'anomalies_detected': 0
        }

        self.latest_insights = []

        # Initialize all components
        self._init_components()

    def _init_components(self):
        """Initialize all system components"""
        logger.info("Initializing enhanced camera system...")

        # Database (initialize first as others may need it)
        if self.config.get('database.enabled', True):
            db_url = self.config.get('database.url', 'sqlite:///data/camera_system.db')
            self.db = DatabaseManager(db_url)

        # Camera setup
        cam_config = self.config.get_camera_config()

        # Check for Reolink integration
        if self.config.get('reolink.enabled', False):
            self._setup_reolink_cameras()
        else:
            self.camera = Camera(**cam_config)

        # Basic detectors
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

        # Advanced AI components
        if self.config.get('ai_features.face_recognition.enabled', True):
            tolerance = self.config.get('ai_features.face_recognition.tolerance', 0.6)
            storage_dir = self.config.get('ai_features.face_recognition.storage_dir', 'data/faces')
            self.face_ai = FaceRecognitionSystem(tolerance=tolerance, storage_dir=storage_dir)
            logger.info("Face recognition AI initialized")

        if self.config.get('ai_features.behavioral_analysis.enabled', True):
            self.behavior = BehavioralAnalysisEngine()
            logger.info("Behavioral analysis engine initialized")

        if self.config.get('ai_features.advanced_analytics.enabled', True):
            pixels_per_meter = self.config.get('ai_features.advanced_analytics.speed_estimation.pixels_per_meter', 50)
            self.analytics = AdvancedAnalytics(pixels_per_meter=pixels_per_meter, fps=cam_config['fps'])
            logger.info("Advanced analytics initialized")

        # Professional speed estimation (new multi-method system)
        self.speed_estimator = PerspectiveSpeedEstimator(
            config=self.config,
            settings_file='data/speed_calibration.json'
        )
        logger.info(f"Professional speed estimation initialized (method: {self.speed_estimator.method})")

        # Recorder
        rec_config = self.config.get_recorder_config()
        self.recorder = VideoRecorder(
            output_dir=rec_config['output_dir'],
            codec=rec_config['codec'],
            fps=cam_config['fps']
        )
        self.event_logger = EventLogger(rec_config['output_dir'])
        self.snapshot_manager = SnapshotManager()

        # Continuous learning
        if self.config.get('ai_features.continuous_learning.enabled', True):
            if all([self.face_ai, self.behavior, self.analytics, self.db]):
                self.learning_system = ContinuousLearningSystem(
                    self.face_ai,
                    self.behavior,
                    self.analytics,
                    self.db
                )
                logger.info("Continuous learning system initialized")

        # Home Assistant integration
        if self.config.get('home_assistant.enabled', False):
            self._setup_home_assistant()

        # Interactive Learning
        if self.config.get('ai_features.interactive_learning.enabled', True):
            self.interactive_learning = InteractiveLearningManager()
            logger.info("Interactive learning initialized")

        logger.info("Enhanced camera system initialization complete")

    def _setup_reolink_cameras(self):
        """Setup Reolink cameras"""
        self.reolink = ReolinkIntegration()

        # Setup NVR if configured
        if self.config.get('reolink.nvr.enabled', False):
            nvr_config = self.config.get('reolink.nvr', {})
            self.reolink.add_nvr(
                nvr_config['ip'],
                nvr_config['username'],
                nvr_config['password']
            )

        # Setup standalone cameras
        cameras = self.config.get('reolink.cameras', [])
        for cam in cameras:
            if cam.get('enabled', False):
                self.reolink.add_standalone_camera(
                    cam['name'],
                    cam['ip'],
                    cam['username'],
                    cam['password'],
                    cam.get('stream_type', 'sub')
                )

        logger.info("Reolink integration configured")

    def _setup_home_assistant(self):
        """Setup Home Assistant MQTT integration"""
        mqtt_config = self.config.get('home_assistant.mqtt', {})
        self.home_assistant = HomeAssistantMQTT(
            broker=mqtt_config.get('broker'),
            port=mqtt_config.get('port', 1883),
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password'),
            device_name=mqtt_config.get('device_name', 'AI Camera System')
        )
        self.home_assistant.connect()
        logger.info("Home Assistant MQTT integration initialized")

    def start(self):
        """Start the enhanced camera system"""
        if self.is_running:
            logger.warning("Camera system already running")
            return False

        logger.info("Starting enhanced camera system...")

        # Start camera
        if not self.camera.start():
            logger.error("Failed to start camera")
            return False

        self.is_running = True
        self.start_time = datetime.now()

        # Start continuous learning
        if self.learning_system:
            self.learning_system.start()

        # Start processing thread
        self.process_thread = Thread(target=self._enhanced_process_loop, daemon=True)
        self.process_thread.start()

        logger.info("Enhanced camera system started successfully")
        return True

    def _enhanced_process_loop(self):
        """Enhanced processing loop with all AI features"""
        frame_count = 0
        last_detection_time = 0
        alert_cooldown = self.config.get('alerts.alert_cooldown', 60)
        process_every_n = self.config.get('performance.process_every_n_frames', 1)

        while self.is_running:
            ret, frame = self.camera.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1
            self.stats['frames_processed'] = frame_count

            if frame_count % process_every_n != 0:
                self.display_frame = frame.copy()
                continue

            display_frame = frame.copy()
            current_time = time.time()

            # Motion detection
            motion_detected = False
            if self.motion_detector:
                motion_detected, _, contours = self.motion_detector.detect(frame)
                if motion_detected:
                    self.stats['motion_events'] += 1
                    display_frame = self.motion_detector.draw_motion(display_frame, contours)

                    if self.home_assistant and self.config.get('home_assistant.publish.motion_detection'):
                        self.home_assistant.publish_motion_detection(True)

            # Object detection with analytics
            detected_people = []
            detected_vehicles = []

            if self.object_detector:
                target_classes = self.config.get('detection.target_classes')
                detections = self.object_detector.detect(frame, target_classes)

                if detections:
                    display_frame = self.object_detector.draw_detections(display_frame, detections)

                    for det in detections:
                        class_name = det['class']
                        self.stats['detections'][class_name] = self.stats['detections'].get(class_name, 0) + 1

                        # Store in database
                        if self.db:
                            self.db.add_detection(
                                object_type=class_name,
                                object_id=f"{class_name}_{frame_count}",
                                confidence=det['confidence'],
                                bbox=det['bbox'],
                                metadata=det,
                                camera_id='default'
                            )

                        # Process vehicles
                        if class_name in ['car', 'truck', 'bus', 'motorcycle']:
                            vehicle_analysis = {}

                            # Use analytics for color detection
                            if self.analytics:
                                vehicle_analysis = self.analytics.analyze_vehicle(
                                    frame,
                                    f"vehicle_{frame_count}",
                                    tuple(map(int, det['bbox']))
                                )

                            # Use professional speed estimator for accurate speed
                            if self.speed_estimator:
                                speed = self.speed_estimator.track_object(
                                    f"vehicle_{frame_count}",
                                    tuple(map(int, det['bbox']))
                                )
                                if speed:
                                    vehicle_analysis['speed'] = speed

                            if vehicle_analysis.get('speed'):
                                # Store vehicle data
                                if self.db:
                                    self.db.add_vehicle_record(
                                        vehicle_id=f"vehicle_{frame_count}",
                                        vehicle_type=class_name,
                                        color=vehicle_analysis.get('color', 'unknown'),
                                        speed=vehicle_analysis['speed'],
                                        metadata=vehicle_analysis
                                    )

                            detected_vehicles.append(vehicle_analysis)

                        # Process people
                        if class_name == 'person':
                            detected_people.append(det)

            # Face recognition for detected people
            recognized_faces = []
            if self.face_ai and detected_people:
                face_detections = self.face_ai.detect_and_recognize(frame)

                if face_detections:
                    display_frame = self.face_ai.draw_faces(display_frame, face_detections)

                    for face in face_detections:
                        person_id = face['person_id']
                        is_recognized = face['name'] != "Unknown"

                        if is_recognized:
                            self.stats['people_recognized'] += 1

                        # Check if unusual time
                        is_unusual = False
                        if self.behavior and is_recognized:
                            is_unusual = self.behavior.is_person_unusual(person_id)

                        # Store in database
                        if self.db:
                            self.db.add_person_appearance(
                                person_id=person_id,
                                person_name=face['name'],
                                confidence=face['confidence'],
                                location={'bbox': face['location']},
                                is_recognized=is_recognized,
                                is_unusual_time=is_unusual
                            )

                        # Record behavioral event
                        if self.behavior:
                            self.behavior.record_event('person_detected', {
                                'person_id': person_id,
                                'confidence': face['confidence'],
                                'location': face['location']
                            })

                        recognized_faces.append(face)

                        # Alert if unusual time
                        if is_unusual:
                            self._add_insight(f"⚠️ {face['name']} detected at unusual time")
                            if self.db:
                                self.db.add_anomaly(
                                    anomaly_type='unusual_time_activity',
                                    severity=0.6,
                                    description=f"{face['name']} appeared at unusual time",
                                    related_objects=[person_id]
                                )

            # Record activities for learning
            if self.behavior:
                if motion_detected:
                    self.behavior.record_event('motion', {'frame': frame_count})
                if detected_vehicles:
                    self.behavior.record_event('vehicle_detected', {'count': len(detected_vehicles)})

            # Publish to Home Assistant
            if self.home_assistant:
                if self.config.get('home_assistant.publish.person_detection'):
                    self.home_assistant.publish_person_detection(
                        len(detected_people),
                        [f['person_id'] for f in recognized_faces]
                    )

                if self.config.get('home_assistant.publish.vehicle_detection'):
                    self.home_assistant.publish_vehicle_detection(len(detected_vehicles), detected_vehicles)

                if self.config.get('home_assistant.publish.speed_data') and detected_vehicles:
                    avg_speed = np.mean([v.get('speed', 0) for v in detected_vehicles if v.get('speed')])
                    self.home_assistant.publish_vehicle_speed(avg_speed)

            # Add info overlay
            display_frame = self._add_enhanced_overlay(display_frame, frame_count)
            self.display_frame = display_frame

            # Recording
            if self.is_recording and self.recorder:
                self.recorder.write_frame(display_frame)

    def _add_enhanced_overlay(self, frame, frame_count):
        """Add enhanced information overlay"""
        height, width = frame.shape[:2]
        overlay = frame.copy()

        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(overlay, timestamp, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Recording indicator
        if self.is_recording:
            cv2.circle(overlay, (width - 30, 30), 10, (0, 0, 255), -1)
            cv2.putText(overlay, "REC", (width - 80, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # AI Status
        if self.learning_system:
            cv2.putText(overlay, "AI LEARNING", (10, height - 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Known people count
        if self.face_ai:
            known_count = len(self.face_ai.known_faces)
            cv2.putText(overlay, f"Known: {known_count}", (10, height - 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        return overlay

    def _add_insight(self, insight: str):
        """Add a new learned insight"""
        self.latest_insights.append({
            'insight': insight,
            'timestamp': datetime.now().isoformat()
        })
        # Keep only latest 10
        self.latest_insights = self.latest_insights[-10:]

    def get_latest_insight(self):
        """Get most recent insight"""
        if self.latest_insights:
            return self.latest_insights[-1]['insight']
        return "System is learning patterns..."

    def get_learned_patterns(self):
        """Get list of learned patterns"""
        patterns = []

        if self.behavior:
            stats = self.behavior.get_statistics()

            # Busiest hours
            if stats.get('busiest_hours'):
                busiest = stats['busiest_hours'][:3]
                pattern_text = ", ".join([f"{h}:00 ({c} events)" for h, c in busiest])
                patterns.append({
                    'title': '📊 Peak Activity Hours',
                    'description': pattern_text
                })

        return patterns

    def start_recording(self):
        """Start video recording"""
        if self.is_recording:
            return False

        if self.recorder and self.display_frame is not None:
            height, width = self.display_frame.shape[:2]
            filepath = self.recorder.start_recording(width, height)

            if filepath:
                self.is_recording = True
                self.stats['recordings'] += 1

                if self.home_assistant:
                    self.home_assistant.publish_recording_status(True)

                return True
        return False

    def stop_recording(self):
        """Stop video recording"""
        if not self.is_recording:
            return None

        if self.recorder:
            filepath = self.recorder.stop_recording()
            self.is_recording = False

            if self.home_assistant:
                self.home_assistant.publish_recording_status(False)

            return filepath
        return None

    def take_snapshot(self):
        """Take a snapshot"""
        if self.display_frame is not None:
            filepath = self.snapshot_manager.save_snapshot(self.display_frame)
            self.stats['snapshots'] += 1
            return filepath
        return None

    def get_display_frame(self):
        """Get current display frame"""
        return self.display_frame

    def get_stats(self):
        """Get system statistics"""
        return self.stats.copy()

    def stop(self):
        """Stop the enhanced camera system"""
        logger.info("Stopping enhanced camera system...")
        self.is_running = False

        if self.is_recording:
            self.stop_recording()

        if self.process_thread:
            self.process_thread.join(timeout=5.0)

        if self.camera:
            self.camera.stop()

        if self.learning_system:
            self.learning_system.stop()

        if self.event_logger:
            self.event_logger.save_events()

        if self.home_assistant:
            self.home_assistant.disconnect()

        logger.info("Enhanced camera system stopped")
