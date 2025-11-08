"""
Advanced analytics: speed estimation, color detection, pattern analysis
"""
import cv2
import numpy as np
import logging
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional
import webcolors
from scipy.spatial import distance as dist

logger = logging.getLogger(__name__)


class VehicleSpeedEstimator:
    """Estimate vehicle speed using optical flow and tracking"""

    def __init__(self, pixels_per_meter=50, fps=30):
        """
        Initialize speed estimator

        Args:
            pixels_per_meter: Calibration factor (pixels per real-world meter)
            fps: Camera frames per second
        """
        self.pixels_per_meter = pixels_per_meter
        self.fps = fps
        self.tracked_objects = {}  # {object_id: {'positions': [], 'timestamps': []}}
        self.speed_history = deque(maxlen=1000)

    def calibrate(self, known_distance_pixels: float, known_distance_meters: float):
        """
        Calibrate the speed estimator with known distance

        Args:
            known_distance_pixels: Distance in pixels
            known_distance_meters: Actual distance in meters
        """
        self.pixels_per_meter = known_distance_pixels / known_distance_meters
        logger.info(f"Speed estimator calibrated: {self.pixels_per_meter:.2f} pixels/meter")

    def track_object(self, object_id: str, bbox: Tuple[int, int, int, int]):
        """
        Track object movement

        Args:
            object_id: Unique object identifier
            bbox: Bounding box (x1, y1, x2, y2)
        """
        # Calculate center point
        x1, y1, x2, y2 = bbox
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        timestamp = datetime.now()

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
            track['speeds'].append(speed)
            return speed

        return None

    def _calculate_speed(self, track: Dict) -> float:
        """
        Calculate speed from position history

        Args:
            track: Track dictionary with positions and timestamps

        Returns:
            Speed in km/h
        """
        positions = track['positions']
        timestamps = track['timestamps']

        if len(positions) < 2:
            return 0.0

        # Calculate distance traveled
        total_distance_pixels = 0
        for i in range(1, len(positions)):
            p1 = positions[i - 1]
            p2 = positions[i]
            distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
            total_distance_pixels += distance

        # Calculate time elapsed
        time_diff = (timestamps[-1] - timestamps[0]).total_seconds()

        if time_diff == 0:
            return 0.0

        # Convert to meters and then to km/h
        distance_meters = total_distance_pixels / self.pixels_per_meter
        speed_mps = distance_meters / time_diff
        speed_kmh = speed_mps * 3.6

        return speed_kmh

    def get_average_speed(self, time_window_minutes: int = 60) -> float:
        """Get average speed over time window"""
        if not self.speed_history:
            return 0.0

        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_speeds = [
            s['speed'] for s in self.speed_history
            if datetime.fromisoformat(s['timestamp']) > cutoff_time
        ]

        if not recent_speeds:
            return 0.0

        return np.mean(recent_speeds)

    def record_speed(self, object_id: str, speed: float, object_type: str = 'vehicle'):
        """Record speed measurement"""
        self.speed_history.append({
            'object_id': object_id,
            'speed': speed,
            'type': object_type,
            'timestamp': datetime.now().isoformat()
        })

    def get_speed_statistics(self) -> Dict:
        """Get speed statistics"""
        if not self.speed_history:
            return {
                'average_speed': 0.0,
                'max_speed': 0.0,
                'min_speed': 0.0,
                'total_vehicles': 0
            }

        speeds = [s['speed'] for s in self.speed_history]

        return {
            'average_speed': float(np.mean(speeds)),
            'max_speed': float(np.max(speeds)),
            'min_speed': float(np.min(speeds)),
            'median_speed': float(np.median(speeds)),
            'total_vehicles': len(self.speed_history)
        }


class ColorDetector:
    """Detect and track colors of objects"""

    def __init__(self):
        """Initialize color detector"""
        self.color_history = deque(maxlen=5000)
        self.color_counts = defaultdict(int)

    def detect_dominant_color(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> str:
        """
        Detect dominant color in bounding box

        Args:
            frame: Input frame
            bbox: Bounding box (x1, y1, x2, y2)

        Returns:
            Color name
        """
        x1, y1, x2, y2 = bbox

        # Extract region of interest
        roi = frame[y1:y2, x1:x2]

        if roi.size == 0:
            return "Unknown"

        # Calculate average color
        avg_color = cv2.mean(roi)[:3]  # BGR

        # Convert to RGB
        rgb_color = (int(avg_color[2]), int(avg_color[1]), int(avg_color[0]))

        # Get closest color name
        color_name = self._get_color_name(rgb_color)

        return color_name

    def _get_color_name(self, rgb_color: Tuple[int, int, int]) -> str:
        """
        Get closest color name from RGB

        Args:
            rgb_color: RGB tuple

        Returns:
            Color name
        """
        min_distance = float('inf')
        closest_name = "Unknown"

        for color_name, color_hex in webcolors.CSS3_HEX_TO_NAMES.items():
            r, g, b = webcolors.hex_to_rgb(color_hex)
            distance = sum((c1 - c2) ** 2 for c1, c2 in zip(rgb_color, (r, g, b)))

            if distance < min_distance:
                min_distance = distance
                closest_name = color_name

        return closest_name

    def record_color(self, color: str, object_type: str = 'vehicle'):
        """Record color detection"""
        self.color_history.append({
            'color': color,
            'type': object_type,
            'timestamp': datetime.now().isoformat()
        })
        self.color_counts[color] += 1

    def get_color_statistics(self) -> Dict:
        """Get color statistics"""
        return {
            'total_detections': len(self.color_history),
            'color_distribution': dict(self.color_counts),
            'most_common_colors': sorted(
                self.color_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }

    def get_colors_by_time(self, hours: int = 24) -> Dict:
        """Get color distribution over time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_colors = [
            c['color'] for c in self.color_history
            if datetime.fromisoformat(c['timestamp']) > cutoff_time
        ]

        color_counts = defaultdict(int)
        for color in recent_colors:
            color_counts[color] += 1

        return dict(color_counts)


class TimeSeriesAnalyzer:
    """Analyze time-based patterns"""

    def __init__(self):
        """Initialize time series analyzer"""
        self.hourly_counts = defaultdict(int)
        self.daily_counts = defaultdict(int)
        self.event_timeline = deque(maxlen=10000)

    def record_event(self, event_type: str, count: int = 1):
        """Record event in timeline"""
        timestamp = datetime.now()

        self.event_timeline.append({
            'type': event_type,
            'count': count,
            'timestamp': timestamp.isoformat(),
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'date': timestamp.date().isoformat()
        })

        # Update counts
        self.hourly_counts[timestamp.hour] += count
        self.daily_counts[timestamp.weekday()] += count

    def get_hourly_distribution(self) -> Dict:
        """Get hourly distribution of events"""
        return dict(self.hourly_counts)

    def get_daily_distribution(self) -> Dict:
        """Get daily distribution (day of week)"""
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return {
            day_names[day]: count
            for day, count in self.daily_counts.items()
        }

    def get_busiest_hours(self, top_n: int = 5) -> List[Tuple[int, int]]:
        """Get busiest hours"""
        return sorted(
            self.hourly_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]

    def get_quietest_hours(self, top_n: int = 5) -> List[Tuple[int, int]]:
        """Get quietest hours"""
        return sorted(
            self.hourly_counts.items(),
            key=lambda x: x[1]
        )[:top_n]

    def predict_next_activity(self) -> str:
        """Predict when next activity is likely based on patterns"""
        current_hour = datetime.now().hour

        # Find most active upcoming hour
        upcoming_hours = [(h, c) for h, c in self.hourly_counts.items() if h > current_hour]

        if not upcoming_hours:
            upcoming_hours = list(self.hourly_counts.items())

        if not upcoming_hours:
            return "Insufficient data for prediction"

        next_busy_hour = max(upcoming_hours, key=lambda x: x[1])[0]

        return f"Next busy period likely at {next_busy_hour}:00"

    def get_timeline_data(self, hours: int = 24) -> List[Dict]:
        """Get event timeline for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        recent_events = [
            e for e in self.event_timeline
            if datetime.fromisoformat(e['timestamp']) > cutoff_time
        ]

        return recent_events


class AdvancedAnalytics:
    """Comprehensive analytics combining all analyzers"""

    def __init__(self, pixels_per_meter=50, fps=30):
        """Initialize advanced analytics"""
        self.speed_estimator = VehicleSpeedEstimator(pixels_per_meter, fps)
        self.color_detector = ColorDetector()
        self.time_analyzer = TimeSeriesAnalyzer()

    def analyze_vehicle(self, frame: np.ndarray, vehicle_id: str, bbox: Tuple[int, int, int, int]):
        """
        Comprehensive vehicle analysis

        Args:
            frame: Input frame
            vehicle_id: Vehicle identifier
            bbox: Bounding box

        Returns:
            Analysis results
        """
        results = {}

        # Speed estimation
        speed = self.speed_estimator.track_object(vehicle_id, bbox)
        if speed:
            results['speed'] = speed
            self.speed_estimator.record_speed(vehicle_id, speed)

        # Color detection
        color = self.color_detector.detect_dominant_color(frame, bbox)
        results['color'] = color
        self.color_detector.record_color(color, 'vehicle')

        # Record in timeline
        self.time_analyzer.record_event('vehicle_detected')

        return results

    def get_comprehensive_statistics(self) -> Dict:
        """Get all statistics"""
        return {
            'speed_stats': self.speed_estimator.get_speed_statistics(),
            'color_stats': self.color_detector.get_color_statistics(),
            'hourly_distribution': self.time_analyzer.get_hourly_distribution(),
            'daily_distribution': self.time_analyzer.get_daily_distribution(),
            'busiest_hours': self.time_analyzer.get_busiest_hours(),
            'quietest_hours': self.time_analyzer.get_quietest_hours(),
            'prediction': self.time_analyzer.predict_next_activity()
        }
