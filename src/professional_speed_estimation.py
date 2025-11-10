"""
Professional Speed Estimation System
Supports multiple calibration methods: simple, zone-based, and homography perspective correction
"""
import cv2
import numpy as np
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Tuple, Optional
import json
import os

logger = logging.getLogger(__name__)


class PerspectiveSpeedEstimator:
    """
    Professional-grade speed estimation with multiple calibration methods

    Methods:
    1. Simple: Single global pixels_per_meter (basic, inaccurate for perspective)
    2. Zoned: Different calibrations for different Y regions (good compromise)
    3. Homography: Full perspective transformation (professional, most accurate)
    """

    def __init__(self, config=None, settings_file='data/speed_calibration.json'):
        """
        Initialize speed estimator

        Args:
            config: System configuration
            settings_file: Path to persistent settings JSON file
        """
        self.settings_file = settings_file
        self.config = config or {}

        # Default settings
        self.method = 'simple'  # simple, zoned, homography
        self.fps = 30
        self.tracked_objects = {}
        self.speed_history = deque(maxlen=1000)

        # Simple calibration
        self.pixels_per_meter = 50

        # Zone-based calibration
        self.zones = []

        # Homography calibration
        self.homography_matrix = None
        self.inverse_homography = None
        self.calibration_points_image = []
        self.calibration_points_world = []

        # Camera parameters (for advanced calibration)
        self.camera_height = None  # meters
        self.camera_distance = None  # meters to road
        self.camera_angle = None  # degrees

        # Load saved settings
        self.load_settings()

    def load_settings(self):
        """Load calibration settings from JSON file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)

                self.method = settings.get('method', 'simple')
                self.fps = settings.get('fps', 30)
                self.pixels_per_meter = settings.get('pixels_per_meter', 50)
                self.zones = settings.get('zones', [])

                # Load homography calibration
                if 'homography' in settings:
                    hom = settings['homography']
                    self.calibration_points_image = hom.get('image_points', [])
                    self.calibration_points_world = hom.get('world_points', [])

                    # Recompute homography matrix if we have points
                    if len(self.calibration_points_image) >= 4:
                        self._compute_homography()

                # Load camera parameters
                self.camera_height = settings.get('camera_height')
                self.camera_distance = settings.get('camera_distance')
                self.camera_angle = settings.get('camera_angle')

                logger.info(f"Loaded speed calibration settings from {self.settings_file}")
                logger.info(f"Method: {self.method}")

            except Exception as e:
                logger.error(f"Failed to load speed settings: {e}")
        else:
            logger.info("No saved speed calibration found, using defaults")

    def save_settings(self):
        """Save calibration settings to JSON file"""
        try:
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)

            settings = {
                'method': self.method,
                'fps': self.fps,
                'pixels_per_meter': self.pixels_per_meter,
                'zones': self.zones,
                'homography': {
                    'image_points': self.calibration_points_image,
                    'world_points': self.calibration_points_world
                },
                'camera_height': self.camera_height,
                'camera_distance': self.camera_distance,
                'camera_angle': self.camera_angle,
                'last_updated': datetime.now().isoformat()
            }

            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

            logger.info(f"Saved speed calibration settings to {self.settings_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save speed settings: {e}")
            return False

    def get_settings(self) -> Dict:
        """Get current settings as dictionary"""
        return {
            'method': self.method,
            'fps': self.fps,
            'pixels_per_meter': self.pixels_per_meter,
            'zones': self.zones,
            'homography': {
                'image_points': self.calibration_points_image,
                'world_points': self.calibration_points_world,
                'is_calibrated': self.homography_matrix is not None
            },
            'camera_height': self.camera_height,
            'camera_distance': self.camera_distance,
            'camera_angle': self.camera_angle
        }

    def update_settings(self, settings: Dict) -> bool:
        """
        Update settings and save

        Args:
            settings: New settings dictionary

        Returns:
            True if successful
        """
        try:
            if 'method' in settings:
                self.method = settings['method']

            if 'fps' in settings:
                self.fps = settings['fps']

            if 'pixels_per_meter' in settings:
                self.pixels_per_meter = settings['pixels_per_meter']

            if 'zones' in settings:
                self.zones = settings['zones']

            if 'homography' in settings:
                hom = settings['homography']
                if 'image_points' in hom:
                    self.calibration_points_image = hom['image_points']
                if 'world_points' in hom:
                    self.calibration_points_world = hom['world_points']

                # Recompute homography if we have enough points
                if len(self.calibration_points_image) >= 4:
                    self._compute_homography()

            if 'camera_height' in settings:
                self.camera_height = settings['camera_height']

            if 'camera_distance' in settings:
                self.camera_distance = settings['camera_distance']

            if 'camera_angle' in settings:
                self.camera_angle = settings['camera_angle']

            # Save to file
            return self.save_settings()

        except Exception as e:
            logger.error(f"Failed to update settings: {e}")
            return False

    def _compute_homography(self):
        """Compute homography matrix from calibration points"""
        try:
            if len(self.calibration_points_image) < 4 or len(self.calibration_points_world) < 4:
                logger.warning("Need at least 4 calibration points for homography")
                return False

            # Convert to numpy arrays
            src_points = np.float32(self.calibration_points_image[:4])
            dst_points = np.float32(self.calibration_points_world[:4])

            # Compute homography matrix
            self.homography_matrix = cv2.getPerspectiveTransform(src_points, dst_points)
            self.inverse_homography = cv2.getPerspectiveTransform(dst_points, src_points)

            logger.info("Homography matrix computed successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to compute homography: {e}")
            return False

    def pixel_to_world(self, pixel_x: float, pixel_y: float) -> Tuple[float, float]:
        """
        Convert pixel coordinates to world coordinates (meters)
        Only works with homography method

        Args:
            pixel_x, pixel_y: Pixel coordinates

        Returns:
            (world_x, world_y) in meters
        """
        if self.homography_matrix is None:
            raise ValueError("Homography not calibrated. Use calibrate_homography() first.")

        # Transform point
        pixel_point = np.array([[[pixel_x, pixel_y]]], dtype=np.float32)
        world_point = cv2.perspectiveTransform(pixel_point, self.homography_matrix)

        return float(world_point[0][0][0]), float(world_point[0][0][1])

    def track_object(self, object_id: str, bbox: Tuple[int, int, int, int]) -> Optional[float]:
        """
        Track object and calculate speed

        Args:
            object_id: Unique identifier
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            Speed in km/h or None
        """
        # Calculate center point
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        timestamp = datetime.now()

        # Initialize track if new
        if object_id not in self.tracked_objects:
            self.tracked_objects[object_id] = {
                'positions': [],
                'timestamps': [],
                'speeds': []
            }

        track = self.tracked_objects[object_id]
        track['positions'].append((center_x, center_y))
        track['timestamps'].append(timestamp)

        # Keep only recent positions (last 2 seconds)
        cutoff_time = timestamp - timedelta(seconds=2)
        while track['timestamps'] and track['timestamps'][0] < cutoff_time:
            track['positions'].pop(0)
            track['timestamps'].pop(0)

        # Calculate speed if we have enough data
        if len(track['positions']) >= 2:
            speed = self._calculate_speed(track)
            if speed is not None:
                track['speeds'].append(speed)
                self._record_speed(object_id, speed)
                return speed

        return None

    def _calculate_speed(self, track: Dict) -> Optional[float]:
        """
        Calculate speed based on selected method

        Args:
            track: Track dictionary with positions and timestamps

        Returns:
            Speed in km/h
        """
        positions = track['positions']
        timestamps = track['timestamps']

        if len(positions) < 2:
            return None

        try:
            if self.method == 'simple':
                return self._calculate_speed_simple(positions, timestamps)
            elif self.method == 'zoned':
                return self._calculate_speed_zoned(positions, timestamps)
            elif self.method == 'homography':
                return self._calculate_speed_homography(positions, timestamps)
            else:
                logger.warning(f"Unknown method {self.method}, using simple")
                return self._calculate_speed_simple(positions, timestamps)

        except Exception as e:
            logger.error(f"Speed calculation failed: {e}")
            return None

    def _calculate_speed_simple(self, positions: List, timestamps: List) -> float:
        """Simple global calibration method"""
        # Calculate total pixel distance
        total_distance_pixels = 0
        for i in range(1, len(positions)):
            p1 = positions[i - 1]
            p2 = positions[i]
            distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            total_distance_pixels += distance

        # Time elapsed
        time_diff = (timestamps[-1] - timestamps[0]).total_seconds()
        if time_diff == 0:
            return 0.0

        # Convert to speed
        distance_meters = total_distance_pixels / self.pixels_per_meter
        speed_mps = distance_meters / time_diff
        speed_kmh = speed_mps * 3.6

        return float(speed_kmh)

    def _calculate_speed_zoned(self, positions: List, timestamps: List) -> float:
        """Zone-based calibration method"""
        total_distance_meters = 0

        for i in range(1, len(positions)):
            p1 = positions[i - 1]
            p2 = positions[i]

            # Pixel distance
            pixel_dist = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

            # Get calibration for average Y position
            avg_y = (p1[1] + p2[1]) / 2
            calibration = self._get_zone_calibration(avg_y)

            # Convert to meters
            meters = pixel_dist / calibration
            total_distance_meters += meters

        # Time elapsed
        time_diff = (timestamps[-1] - timestamps[0]).total_seconds()
        if time_diff == 0:
            return 0.0

        speed_mps = total_distance_meters / time_diff
        speed_kmh = speed_mps * 3.6

        return float(speed_kmh)

    def _calculate_speed_homography(self, positions: List, timestamps: List) -> float:
        """Homography perspective correction method"""
        if self.homography_matrix is None:
            logger.warning("Homography not calibrated, falling back to simple method")
            return self._calculate_speed_simple(positions, timestamps)

        # Convert all positions to world coordinates
        world_positions = []
        for px, py in positions:
            try:
                wx, wy = self.pixel_to_world(px, py)
                world_positions.append((wx, wy))
            except Exception as e:
                logger.error(f"Pixel to world conversion failed: {e}")
                return self._calculate_speed_simple(positions, timestamps)

        # Calculate distance in real meters
        total_distance = 0
        for i in range(1, len(world_positions)):
            p1 = world_positions[i - 1]
            p2 = world_positions[i]
            distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            total_distance += distance

        # Time elapsed
        time_diff = (timestamps[-1] - timestamps[0]).total_seconds()
        if time_diff == 0:
            return 0.0

        speed_mps = total_distance / time_diff
        speed_kmh = speed_mps * 3.6

        return float(speed_kmh)

    def _get_zone_calibration(self, y_pixel: float) -> float:
        """Get calibration factor for given Y position"""
        if not self.zones:
            return self.pixels_per_meter

        for zone in self.zones:
            y_min, y_max = zone['y_range']
            if y_min <= y_pixel <= y_max:
                return zone['pixels_per_meter']

        # Default if no zone matches
        return self.pixels_per_meter

    def _record_speed(self, object_id: str, speed: float):
        """Record speed measurement"""
        self.speed_history.append({
            'object_id': object_id,
            'speed': speed,
            'timestamp': datetime.now().isoformat(),
            'method': self.method
        })

    def get_speed_statistics(self) -> Dict:
        """Get speed statistics"""
        if not self.speed_history:
            return {
                'average_speed': 0.0,
                'max_speed': 0.0,
                'min_speed': 0.0,
                'median_speed': 0.0,
                'total_vehicles': 0,
                'method': self.method
            }

        speeds = [s['speed'] for s in self.speed_history if s['speed'] > 0]

        if not speeds:
            return {
                'average_speed': 0.0,
                'max_speed': 0.0,
                'min_speed': 0.0,
                'median_speed': 0.0,
                'total_vehicles': 0,
                'method': self.method
            }

        return {
            'average_speed': float(np.mean(speeds)),
            'max_speed': float(np.max(speeds)),
            'min_speed': float(np.min(speeds)),
            'median_speed': float(np.median(speeds)),
            'total_vehicles': len(speeds),
            'method': self.method
        }

    def clear_tracking(self):
        """Clear all tracking data"""
        self.tracked_objects.clear()
        logger.info("Cleared tracking data")

    def get_calibration_guide(self) -> Dict:
        """
        Get calibration instructions for current method

        Returns:
            Dictionary with step-by-step instructions
        """
        guides = {
            'simple': {
                'name': 'Simple Global Calibration',
                'difficulty': 'Easy',
                'accuracy': 'Low (perspective errors)',
                'steps': [
                    'Measure a known distance on the road (e.g., 5 meters)',
                    'In a camera frame, measure the pixel distance',
                    'Calculate: pixels_per_meter = measured_pixels / actual_meters',
                    'Enter the value in settings',
                    'Note: Accuracy decreases with distance from camera'
                ],
                'example': 'If 5 meters = 250 pixels, then pixels_per_meter = 50'
            },
            'zoned': {
                'name': 'Zone-Based Calibration',
                'difficulty': 'Medium',
                'accuracy': 'Good (better than simple)',
                'steps': [
                    'Divide the camera view into 3-5 horizontal zones',
                    'For each zone, measure a known distance',
                    'Calculate pixels_per_meter for each zone',
                    'Define Y pixel ranges for each zone',
                    'Zones closer to camera have higher pixels_per_meter'
                ],
                'example': 'Near zone (y:480-720): 80 ppm, Far zone (y:0-240): 25 ppm'
            },
            'homography': {
                'name': 'Homography Perspective Correction',
                'difficulty': 'Advanced',
                'accuracy': 'Excellent (professional grade)',
                'steps': [
                    'Mark or identify 4 reference points on the road forming a rectangle',
                    'Measure the real-world coordinates (in meters)',
                    'Click the 4 corresponding points in the camera view',
                    'System automatically computes perspective transform',
                    'All speed measurements are now perspective-corrected'
                ],
                'example': '4 corners of a 5m x 2.5m parking space',
                'tips': [
                    'Use a rectangle parallel to the road',
                    'Points should be clearly visible',
                    'Larger reference area = better accuracy',
                    'Avoid areas with lens distortion (edges of frame)'
                ]
            }
        }

        return guides.get(self.method, guides['simple'])
